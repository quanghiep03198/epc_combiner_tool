import asyncio
import asyncio
from database import get_raw_sql
from PyQt6.QtSql import *
from helpers.logger import logger
from pathlib import Path
from database import DATA_SOURCE_ERP


class OrderRepository:

    @staticmethod
    def get_order_detail(mo_no: str):
        results = []
        try:
            current_dir = Path(__file__).parent.resolve()
            sql_file_path = current_dir / "./sql/get_order_information.sql"
            # sql_statement = await asyncio.to_thread(get_raw_sql, sql_file_path)
            sql_statement = get_raw_sql(sql_file_path)
            query = QSqlQuery(DATA_SOURCE_ERP)
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
