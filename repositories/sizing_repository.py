from PyQt6.QtSql import *
from helpers.logger import logger
from pathlib import Path
from database import DatabaseService, DATA_SOURCE_ERP


class SizingRepository:
    __sql_file_path = Path(__file__).parent.resolve() / "./sql/get_size_qty.sql"

    @staticmethod
    def find_size_qty(params: dict) -> list[dict]:
        result = []
        try:
            sql_statement = DatabaseService.get_raw_sql(
                SizingRepository.__sql_file_path
            )
            query = QSqlQuery(DATA_SOURCE_ERP)
            query.prepare(sql_statement)
            query.bindValue(":mo_no", params["mo_no"])
            # if params["mo_noseq"] is not None:
            #     query.bindValue(":mo_noseq", params["mo_noseq"])
            # else:
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
            logger.debug(f"Result: {result}")
        except Exception as e:
            logger.error(f"Error finding sizing detail: {e}")
        finally:
            return result
