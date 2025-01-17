import asyncio
from database import get_raw_sql
from PyQt6.QtSql import *
from helpers.logger import logger
from pathlib import Path
from database import DATA_SOURCE_ERP


class SizingRepository:

    @staticmethod
    def find_size_qty(mo_no: str) -> list[dict]:
        result = []
        try:
            current_dir = Path(__file__).parent.resolve()
            sql_file_path = current_dir / "./sql/get_size_qty.sql"
            # sql_statement = await asyncio.to_thread(get_raw_sql, sql_file_path)
            sql_statement = get_raw_sql(sql_file_path)
            query = QSqlQuery(DATA_SOURCE_ERP)
            query.prepare(sql_statement)
            query.bindValue(":mo_no", mo_no)
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
            logger.debug(f"Found sizing detail: {result}")
        except Exception as e:
            logger.error(f"Error finding sizing detail: {e}")
        finally:
            return result
