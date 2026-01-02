from PyQt6.QtSql import *
from pathlib import Path
from database import db_service, DatabaseConnection
from contexts.auth_context import auth_context
from helpers.logger import logger
from i18n import I18nService


class StationRepository:
    __compensatable_station_list_sql_file_path = (
        Path(__file__).parent.resolve() / "./sql/get_station.sql"
    )

    __station_history_sql_file_path: str = (
        Path(__file__).parent.resolve() / "./sql/station_history.sql"
    )

    __factory_stations: list[dict] = [
        {"station_no": "departments.sewing", "station_seq_no": 2},
        {"station_no": "departments.shaping", "station_seq_no": 3},
        {
            "station_no": "departments.central_warehouse",
            "station_seq_no": 4,
        },
        {"station_no": "departments.assembly_entry", "station_seq_no": 5},
        {"station_no": "departments.assembly_label_collection", "station_seq_no": 6},
    ]

    @staticmethod
    def get_stations() -> list[dict]:
        if auth_context.get("factory_code") != "VA1":
            return [
                station
                for station in StationRepository.__factory_stations
                if station["station_seq_no"] != 3 or station["station_seq_no"] != 4
            ]

        return StationRepository.__factory_stations

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
