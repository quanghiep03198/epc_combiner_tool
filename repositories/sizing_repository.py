import asyncio
from database import get_raw_sql
from PyQt6.QtSql import *
from helpers.logger import logger
from pathlib import Path


class SizingRepository:
    def __init__(self, data_source_erp):
        self.data_source_erp = data_source_erp

    async def find_size_qty(self, mo_no: str) -> QSqlQuery:
        result = []
        try:
            current_dir = Path(__file__).parent.resolve()
            sql_file_path = current_dir / "./sql/get_size_qty.sql"
            sql_statement = await asyncio.to_thread(get_raw_sql, sql_file_path)
            query = QSqlQuery(self.data_source_erp)
            query.prepare(sql_statement)
            query.bindValue(":mo_no", mo_no)
            query.exec()
            while query.next():
                result.append(
                    {
                        "size_code": query.value("size_code"),
                        "size_numcode": query.value("size_numcode"),
                        "size_qty": query.value("size_qty"),
                    }
                )
        except Exception as e:
            logger.error(f"Error finding sizing detail: {e}")
        finally:
            return result
