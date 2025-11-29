from PyQt6.QtSql import *
from pathlib import Path
from database import db_service, DatabaseConnection


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
