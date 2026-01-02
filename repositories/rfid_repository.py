from PyQt6.QtSql import *
from helpers.logger import logger
from contexts.combine_form_context import combine_form_context
from database import db_service, DatabaseConnection
from contexts.auth_context import auth_context
from helpers.disutils import strtobool
import json
from constants import CombineAction
from pathlib import Path
from repositories.station_repository import StationRepository
from PyQt6.QtCore import QDateTime
from i18n import I18nService


class RFIDRepository:
    __epc_trace_history_sql_file_path = (
        Path(__file__).parent.resolve() / "./sql/epc_trace_history.sql"
    )

    @staticmethod
    def check_reasonable_combination(data: list[dict]) -> list[dict]:
        result: list[dict] = []
        try:
            connection = db_service.get_connection(DatabaseConnection.DATA_LAKE)
            query = QSqlQuery(connection)
            epc_list = ",".join([f"'{item['EPC_Code']}'" for item in data])
            query.prepare(
                f"""--sql
                SELECT EPC_Code, 
                    CASE WHEN CAST(ri_date AS DATE) <= CAST(DATEADD(DAY, -2, GETDATE()) AS DATE) 
                    THEN 't' ELSE 'f' END AS recombinable
                FROM DV_DATA_LAKE.dbo.dv_rfidmatchmst
                WHERE EPC_Code IN ({epc_list})
                    AND ri_cancel = 0
                """
            )
            query.exec()
            while query.next():
                result.append(
                    {
                        "EPC_Code": query.value("EPC_Code"),
                        "recombinable": strtobool(query.value("recombinable")),
                    }
                )
            return result
        except:
            raise Exception("Error checking reasonable combination")

    @staticmethod
    def reset_and_add_combinations(data: list[dict]) -> int | None:
        connection = None
        query = None
        try:
            connection = db_service.get_connection(DatabaseConnection.DATA_LAKE)

            # Bắt đầu transaction
            if not connection.transaction():
                raise Exception("Failed to start transaction")

            query = QSqlQuery(connection)
            epc_params_str = ",".join([f"'{item['EPC_Code']}'" for item in data])
            logger.info(f"EPC Params String: >> {epc_params_str}")
            fallback_station_no = "%s_%s" % (auth_context.get("factory_code"), "PA103")

            # Force end EPC's lifecycle
            query.prepare(
                f"""-- sql
                WITH CTE_MatchKeys AS (
                    SELECT a.keyid as matchkeyid 
                    FROM DV_DATA_LAKE.dbo.dv_rfidmatchmst a
                    INNER JOIN DV_DATA_LAKE.dbo.dv_RFIDrecordmst b
                        ON a.EPC_Code = b.EPC_Code
                        AND a.keyid = b.matchkeyid
                    WHERE a.EPC_Code IN ({epc_params_str})
                        AND a.ri_cancel = 0  
                        AND b.stationNO NOT LIKE '%P%103'
                )
                UPDATE DV_DATA_LAKE.dbo.dv_RFIDrecordmst
                SET stationNO = (
                    SELECT COALESCE(
                        -- find stationNO by both "mo_no" and "size_code"
                        (
                            SELECT TOP 1 a.stationNO
                            FROM DV_DATA_LAKE.dbo.dv_RFIDrecordmst a, DV_DATA_LAKE.dbo.dv_RFIDrecordmst b 
                            WHERE b.stationNO NOT LIKE '%P%103' 
                            AND a.mo_no = b.mo_no  
                            AND a.size_code = b.size_code
                            AND a.stationNO <> b.stationNO
                            AND a.EPC_Code <> b.EPC_Code 
                            AND b.EPC_Code IN ({epc_params_str})
                            ORDER BY a.record_time DESC
                        ), 
                        -- else use the fallback stationNO
                        '{fallback_station_no}'
                        ) AS stationNO
                    ),              
                    user_code_updated = '{combine_form_context.get("user_code_updated")}',
                    user_name_updated = '{combine_form_context.get("user_name_updated")}',
                    record_time = DATEADD(DAY, -7, GETDATE()),
                    remark = 'Forced lifecycle end by {combine_form_context.get("user_name_updated")}'
                WHERE matchkeyid IN (SELECT matchkeyid FROM CTE_MatchKeys)
                ;
                """
            )

            if not query.exec():
                raise Exception(query.lastError().text())

            # Cancel old records
            query.prepare(
                f"""--sql          
                UPDATE DV_DATA_LAKE.dbo.dv_rfidmatchmst
                SET ri_cancel = 1, 
                    ri_reason_cancel = 'EPC lifecycle ended', 
                    ri_cancel_date = GETDATE(),
                    user_code_updated = '{combine_form_context.get("user_code_updated")}',
                    user_name_updated = '{combine_form_context.get("user_name_updated")}'
                WHERE EPC_Code IN ({epc_params_str})
                    AND ri_cancel = 0
                    AND sole_tag = 'A'
                ;
                """
            )

            if not query.exec():
                raise Exception(query.lastError().text())

            # Insert new records
            # Convert data to JSON format
            json_data = json.dumps(obj=data, ensure_ascii=False).replace("'", "''")

            # Use the JSON to perform an insert-select operation
            query.prepare(
                f"""--sql
                INSERT INTO DV_DATA_LAKE.dbo.dv_rfidmatchmst (
                    EPC_Code, mo_no, mo_noseq, mat_code, or_no, or_custpo, 
                    shoestyle_codefactory, cust_shoestyle, size_numcode, size_code, size_qty,
                    factory_code_orders, factory_name_orders, factory_code_produce, factory_name_produce, 
                    ri_date, ri_cancel, ri_type, ri_foot, 
                    sole_tag, sole_tag_rate, sole_tag_round, 
                    user_code_created, user_name_created, 
                    dept_code, dept_name,
                    isactive, remark
                )
                SELECT 
                    JSON_VALUE(value, '$.EPC_Code') AS EPC_Code,
                    JSON_VALUE(value, '$.mo_no') AS mo_no,
                    JSON_VALUE(value, '$.mo_noseq') AS mo_noseq,
                    JSON_VALUE(value, '$.mat_code') AS mat_code,
                    JSON_VALUE(value, '$.or_no') AS or_no,
                    JSON_VALUE(value, '$.or_custpo') AS or_custpo,
                    JSON_VALUE(value, '$.shoestyle_codefactory') AS shoestyle_codefactory,
                    JSON_VALUE(value, '$.cust_shoestyle') AS cust_shoestyle,
                    JSON_VALUE(value, '$.size_numcode') AS size_numcode,
                    JSON_VALUE(value, '$.size_code') AS size_code,
                    CAST(JSON_VALUE(value, '$.size_qty') AS INT) AS size_qty,
                    JSON_VALUE(value, '$.factory_code_orders') AS factory_code_orders,
                    JSON_VALUE(value, '$.factory_name_orders') AS factory_name_orders,
                    JSON_VALUE(value, '$.factory_code_produce') AS factory_code_produce,
                    JSON_VALUE(value, '$.factory_name_produce') AS factory_name_produce,
                    GETDATE() AS ri_date,
                    CAST(JSON_VALUE(value, '$.ri_cancel') AS INT) AS ri_cancel,
                    JSON_VALUE(value, '$.ri_type') AS ri_type,
                    JSON_VALUE(value, '$.ri_foot') AS ri_foot,
                    JSON_VALUE(value, '$.sole_tag') AS sole_tag,
                    CAST(JSON_VALUE(value, '$.sole_tag_rate') AS FLOAT) AS sole_tag_rate,
                    CAST(JSON_VALUE(value, '$.sole_tag_round') AS FLOAT) AS sole_tag_round,
                    JSON_VALUE(value, '$.user_code_created') AS user_code_created,
                    JSON_VALUE(value, '$.user_name_created') AS user_name_created,
                    JSON_VALUE(value, '$.dept_code') AS dept_code,
                    JSON_VALUE(value, '$.dept_name') AS dept_name,
                    JSON_VALUE(value, '$.isactive') AS isactive,
                    JSON_VALUE(value, '$.remark') AS remark
                FROM OPENJSON('{json_data}')
                ;
                """
            )

            if not query.exec():
                raise Exception(query.lastError().text())

            if combine_form_context["ri_type"] == CombineAction.COMPENSATE.value:
                station_history = StationRepository.get_station_history(
                    mo_no=combine_form_context["mo_no"],
                    size_numcode=combine_form_context["size_numcode"],
                    station_seq_no=combine_form_context["station_seq_no"],
                )
                logger.debug(f"Station history: {station_history}")

                # Get max station_seq_no in trace_history_stations
                max_station_seq_no = max(
                    station.get("station_seq_no", 0) for station in station_history
                )
                logger.debug(f"Max station_seq_no: {max_station_seq_no}")

                """
                Validate missing station history before compensation point
                If missing, raise exception to rollback transaction
                """
                if combine_form_context["station_seq_no"] > max_station_seq_no:
                    logger.error(
                        "Cannot compensate: Missing station history before compensation point."
                    )
                    raise Exception(
                        I18nService.t("notification.missing_station_point_history")
                    )
                # Insert trace history for each station before compensation point
                json_epcs_codes = json.dumps(
                    obj=[item["EPC_Code"] for item in data],
                    ensure_ascii=False,
                )
                # Filter stations with station_seq_no < compensation point
                trace_history_stations = [
                    station
                    for station in station_history
                    if station.get("station_seq_no", 0)
                    < combine_form_context["station_seq_no"]
                ]
                logger.debug(f"Actual trace history stations: {trace_history_stations}")
                # target_station: str = combine_form_context["station_no"]
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
                            RFIDRepository.trace_history_at_station(
                                query_runner=query,
                                json_epcs_codes=json_epcs_codes,
                                station_no=trace_station_no,
                                inoutbound_type=type,
                                record_time=last_record_time,
                                # target_station_no=target_station,
                            )
                    else:
                        RFIDRepository.trace_history_at_station(
                            query_runner=query,
                            json_epcs_codes=json_epcs_codes,
                            station_no=trace_station_no,
                            inoutbound_type="A",
                            record_time=last_record_time,
                            # target_station_no=target_station,
                        )

            connection.commit()
            return query.numRowsAffected()
        except Exception as e:
            # Rollback transaction nếu có lỗi
            if connection is not None:
                connection.rollback()
                logger.error(f"Transaction rolled back due to error: {e}")
            else:
                logger.error(f"Connection not established: {e}")
            raise Exception(e)
        finally:
            if query is not None:
                query.finish()

    @staticmethod
    def trace_history_at_station(
        query_runner: QSqlQuery,
        json_epcs_codes: str,
        station_no: str,
        inoutbound_type: str,
        record_time: str,
        # target_station_no: str,
    ) -> int:
        query_runner.prepare(
            db_service.get_raw_sql(RFIDRepository.__epc_trace_history_sql_file_path)
        )
        query_runner.bindValue(":json_epcs_codes", json_epcs_codes)
        query_runner.bindValue(":factory_code", auth_context.get("factory_code"))
        query_runner.bindValue(":station_no", station_no)
        query_runner.bindValue(":inoutbound_type", inoutbound_type)
        query_runner.bindValue(":record_time", record_time)
        query_runner.bindValue(":username", auth_context.get("user_code"))
        # query_runner.bindValue(":target_station_no", target_station_no)

        if not query_runner.exec():
            raise Exception(query_runner.lastError().text())

        return query_runner.numRowsAffected()
