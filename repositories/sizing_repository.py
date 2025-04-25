from PyQt6.QtSql import *
from helpers.logger import logger
from pathlib import Path
from database import DatabaseService, DataSources, DatabaseConnection
from helpers.configuration import ConfigService

configuration = ConfigService.load_configs()


class SizingRepository:
    __sql_file_path = Path(__file__).parent.resolve() / "./sql/get_size_qty.sql"

    __ERP_DB_CONN__ = DatabaseService.connnect_database(
        server=configuration.get("DB_SERVER"),
        database=DataSources.ERP.value,
        connection_name=f"[SizingRepository]{DatabaseConnection.ERP.value}",
    )
    """
        A new instance of connection to ERP database to execute parallel queries
    """

    @staticmethod
    def find_size_qty(params: dict) -> list[dict]:
        result = []
        query = None
        try:
            sql_statement = DatabaseService.get_raw_sql(
                SizingRepository.__sql_file_path
            )
            query = QSqlQuery(SizingRepository.__ERP_DB_CONN__)
            query.prepare(sql_statement)
            query.bindValue(":mo_no", params["mo_no"])
            if params["mo_noseq"] == "all":
                query.bindValue(":mo_noseq", None)
            else:
                query.bindValue(":mo_noseq", params["mo_noseq"])
            query.exec()
            while query.next():
                result.append(
                    {
                        "size_code": query.value("size_code"),
                        "size_numcode": query.value("size_numcode"),
                        "size_qty": query.value("size_qty"),
                        "combined_qty": query.value("combined_qty"),
                        "in_use_qty": query.value("in_use_qty"),
                        "compensated_qty": query.value("compensated_qty"),
                        "cancelled_qty": query.value("cancelled_qty"),
                    }
                )
        except Exception as e:
            logger.error(f"Error finding sizing detail: {e}")
        finally:
            if query is not None:
                query.finish()
            return result
