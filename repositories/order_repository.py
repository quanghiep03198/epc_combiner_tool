import asyncio
import asyncio
from database import get_raw_sql
from PyQt6.QtSql import *
from helpers.logger import logger
from pathlib import Path


class OrderRepository:
    def __init__(self, data_source_erp):
        self.data_source_erp = data_source_erp

    async def get_order_detail(self, mo_no: str):
        results = []
        try:
            current_dir = Path(__file__).parent.resolve()
            sql_file_path = current_dir / "./sql/get_order_information.sql"
            sql_statement = await asyncio.to_thread(get_raw_sql, sql_file_path)

            query = QSqlQuery(self.data_source_erp)
            query.prepare(sql_statement)
            query.bindValue(":mo_no", mo_no)
            query.exec()
            while query.next():
                print(query.record())
                results.append(
                    {
                        "shoestyle_codefactory": query.value("shoestyle_codefactory"),
                        "mo_no": query.value("mo_no"),
                        "mat_code": query.value("mat_code"),
                        "cust_shoestyle": query.value("cust_shoestyle"),
                        "mo_noseq": query.value("mo_noseq"),
                        "or_no": query.value("or_no"),
                        "or_custpo": query.value("or_custpo"),
                        "size_qty": query.value("size_qty"),
                    }
                )

        except Exception as e:
            logger.error(f"Error finding order detail: {e}")
        finally:
            return results
