from PyQt6.QtSql import *
from helpers.logger import logger
from pathlib import Path
from database import db_service, DataSources, DatabaseConnection
from helpers.configuration import ConfigService

# from database import DATA_SOURCE_ERP

configuration = ConfigService.load_configs()


class SizingRepository:
    __sql_file_path = Path(__file__).parent.resolve() / "./sql/get_size_qty.sql"

    @staticmethod
    def find_size_qty(params: dict) -> list[dict]:
        return db_service.execute_query(
            connection_type=DatabaseConnection.ERP,
            sql_query=db_service.get_raw_sql(SizingRepository.__sql_file_path),
            bind_values={
                "mo_no": params["mo_no"],
                "mo_noseq": None if params["mo_noseq"] == "all" else params["mo_noseq"],
            },
        )
