import json
from pathlib import Path

from PyQt6.QtCore import QDateTime
from PyQt6.QtSql import *

from constants import CombineAction, FactoryCodes
from contexts.auth_context import auth_context
from contexts.combine_form_context import combine_form_context
from database import DatabaseConnection, db_service
from helpers.disutils import strtobool
from helpers.logger import logger
from i18n import I18nService
from repositories.station_repository import StationRepository


class RFIDRepository:

    @staticmethod
    def check_reasonable_combination(data: list[dict]) -> list[dict]:
        if not data:
            return []

        epc_list = ",".join([f"{item['EPC_Code']}" for item in data])
        result = db_service.execute_query(
            connection_type=DatabaseConnection.DATA_LAKE,
            sql_query=f"""--sql
                SELECT EPC_Code, 
                    CASE WHEN CAST(ri_date AS DATE) <= CAST(DATEADD(DAY, -2, GETDATE()) AS DATE) 
                    THEN 't' ELSE 'f' END AS recombinable
                FROM DV_DATA_LAKE.dbo.dv_rfidmatchmst
                WHERE EPC_Code IN (
                    SELECT LTRIM(RTRIM(value))
                    FROM STRING_SPLIT(CAST(:epc_list AS NVARCHAR(MAX)), ',')
                )
                    AND ri_cancel = 0
            """,
            bind_values={"epc_list": epc_list},
        )

        if result is None:
            raise Exception("Failed to check reasonable combination")

        return list(
            map(
                lambda row: {
                    "EPC_Code": row["EPC_Code"],
                    "recombinable": strtobool(row["recombinable"]),
                },
                result,
            )
        )

    @staticmethod
    def reset_and_add_combinations(data: list[dict]) -> int | None:
        connection = None
        try:
            connection = db_service.get_connection(DatabaseConnection.DATA_LAKE)
            
            if not connection.transaction():
                raise Exception("Failed to start transaction")

            epc_params_str = ",".join([f"{item['EPC_Code']}" for item in data])

            # region Producing lifecycle

            # * Only apply epc's ending producing lifecycle for all factories except for Cambodia (CA1)
            should_compensate_assembly = (
                auth_context.get("factory_code") == FactoryCodes.CA1.value
            )
            if should_compensate_assembly:
                compensate_assembly_result = db_service.execute_non_query(
                    connection_type=DatabaseConnection.DATA_LAKE,
                    sql_query=db_service.get_raw_sql(
                        Path(__file__).parent.resolve()
                        / "./sql/compensate_assembly.sql"
                    ),
                    bind_values={
                        "username": auth_context.get("user_code"),
                        "factory_code": auth_context.get("factory_code"),
                        "pending_combine_epcs": epc_params_str,
                    },
                )

                if compensate_assembly_result == -1:
                    raise Exception("Failed to end producing lifecycle for EPCs")

            # endregion

            # region Common logic

            # Cancel old records
            cancel_old_epcs_result: int = db_service.execute_non_query(
                connection_type=DatabaseConnection.DATA_LAKE,
                sql_query=db_service.get_raw_sql(
                    Path(__file__).parent.resolve() / "./sql/cancel_old_match.sql"
                ),
                bind_values={
                    "pending_combine_epcs": epc_params_str,
                    "username": auth_context.get("user_code"),
                },
            )

            if cancel_old_epcs_result == -1:
                raise Exception("Failed to cancel old match records")

            # Insert new records
            insert_result = db_service.execute_non_query(
                connection_type=DatabaseConnection.DATA_LAKE,
                sql_query=db_service.get_raw_sql(
                    Path(__file__).parent.resolve() / "./sql/insert_epc_match.sql"
                ),
                bind_values={
                    "json_data": json.dumps(obj=data, ensure_ascii=False).replace(
                        "'", "''"
                    )
                },
            )

            if insert_result == -1:
                raise Exception("Failed to insert new match records")

            # endregion

            # region Compensation logic
            if combine_form_context["ri_type"] == CombineAction.COMPENSATE.value:
                station_history = StationRepository.get_station_history(
                    mo_no=combine_form_context["mo_no"],
                    size_numcode=combine_form_context["size_numcode"],
                    station_seq_no=combine_form_context["station_seq_no"],
                )

                # * Get max station_seq_no in trace_history_stations
                max_station_seq_no = max(
                    station.get("station_seq_no", 0) for station in station_history
                )

                """
                * Validate missing station history before compensation point
                * If missing, raise exception to rollback transaction
                """
                if combine_form_context["station_seq_no"] > max_station_seq_no:
                    logger.error(
                        "Cannot compensate: Missing station history before compensation point."
                    )
                    raise Exception(
                        I18nService.t("notification.missing_station_point_history")
                    )
                # * Insert trace history for each station before compensation point
                json_epcs_codes = json.dumps(
                    obj=[item["EPC_Code"] for item in data],
                    ensure_ascii=False,
                )
                # * Filter stations with station_seq_no < compensation point
                trace_history_stations = [
                    station
                    for station in station_history
                    if station.get("station_seq_no", 0)
                    < combine_form_context["station_seq_no"]
                ]

                trace_history_result: int = 0

                for station in trace_history_stations:
                    inoutbound_types: str | None = None
                    trace_station_no: str = station.get("station_no", "")
                    last_record_time: str = station.get(
                        "last_record_time",
                        (
                            QDateTime.currentDateTime()
                            .addDays(-7)
                            .toString("yyyy-MM-dd HH:mm:ss")
                        ),
                    )

                    if "IH" in trace_station_no:
                        inoutbound_types = (
                            ["A", "B"]
                            if combine_form_context.get("station_seq_no")
                            > station.get("station_seq_no", 0)
                            else ["A"]
                        )
                        for type in inoutbound_types:
                            trace_history_result = RFIDRepository.trace_history_at_station(
                                json_epcs_codes=json_epcs_codes,
                                station_no=trace_station_no,
                                inoutbound_type=type,
                                record_time=last_record_time,
                                # target_station_no=target_station,
                            )
                            if trace_history_result == -1:
                                break
                    else:
                        trace_history_result = RFIDRepository.trace_history_at_station(
                            json_epcs_codes=json_epcs_codes,
                            station_no=trace_station_no,
                            inoutbound_type="A",
                            record_time=last_record_time,
                        )
                        if trace_history_result == -1:
                            break

                if trace_history_result == -1:
                    raise Exception(
                        "Failed to insert trace history for stations before compensation point"
                    )

            # endregion
            connection.commit()

            return insert_result

        except Exception as e:
            if connection is not None:
                connection.rollback()
                logger.error(f"Transaction rolled back due to error: {e}")
            else:
                logger.error(f"Connection not established: {e}")
            raise Exception(e)

    @staticmethod
    def trace_history_at_station(
        json_epcs_codes: str,
        station_no: str,
        inoutbound_type: str,
        record_time: str,
    ) -> int:
        result = db_service.execute_non_query(
            connection_type=DatabaseConnection.DATA_LAKE,
            sql_query=db_service.get_raw_sql(
                Path(__file__).parent.resolve() / "./sql/epc_trace_history.sql"
            ),
            bind_values={
                "json_epcs_codes": json_epcs_codes,
                "factory_code": auth_context.get("factory_code"),
                "station_no": station_no,
                "inoutbound_type": inoutbound_type,
                "record_time": record_time,
                "username": auth_context.get("user_code"),
            },
        )

        return result
