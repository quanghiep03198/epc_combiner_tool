from PyQt6.QtSql import *
from pathlib import Path
from database import db_service, DatabaseConnection
from contexts.auth_context import auth_context
from helpers.logger import logger


class StationRepository:
    __compensatable_station_list_sql_file_path = (
        Path(__file__).parent.resolve() / "./sql/get_station.sql"
    )

    __station_history_sql_file_path: str = (
        Path(__file__).parent.resolve() / "./sql/station_history.sql"
    )

    @staticmethod
    def get_stations() -> list[dict]:
        return db_service.execute_query(
            connection_type=DatabaseConnection.DATA_LAKE,
            sql_query=db_service.get_raw_sql(
                StationRepository.__compensatable_station_list_sql_file_path
            ),
            bind_values={
                "factory_code": auth_context["factory_code"],
            },
        )

    @staticmethod
    def get_station_history(
        mo_no: str, size_numcode: str, station_seq_no: int
    ) -> list[dict]:

        try:
            return db_service.execute_query(
                connection_type=DatabaseConnection.DATA_LAKE,
                sql_query=db_service.get_raw_sql(
                    StationRepository.__station_history_sql_file_path
                ),
                bind_values={
                    "mo_no": mo_no,
                    "size_numcode": size_numcode,
                    "station_seq_no": station_seq_no,
                },
            )
        except Exception as e:
            logger.error(f"Error fetching station history: {e}")
            raise Exception(e.args[0])
