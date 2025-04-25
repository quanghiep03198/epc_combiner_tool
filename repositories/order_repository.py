from PyQt6.QtSql import *
from helpers.logger import logger
from pathlib import Path
from database import DatabaseService, DATA_SOURCE_ERP


class OrderRepository:
    __sql_file_path = (
        Path(__file__).parent.resolve() / "./sql/get_order_information.sql"
    )

    @staticmethod
    def get_order_detail(params: dict):
        results = []
        query = QSqlQuery(DATA_SOURCE_ERP)
        try:
            sql_statement = DatabaseService.get_raw_sql(OrderRepository.__sql_file_path)
            query.prepare(sql_statement)
            query.bindValue(":mo_no", params["mo_no"])
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
            query.finish()
            return results
