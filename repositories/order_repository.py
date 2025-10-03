from PyQt6.QtSql import *
from helpers.logger import logger
from pathlib import Path
from database import db_service, DatabaseConnection
from contexts.auth_context import auth_context


class OrderRepository:
    __sql_file_path = (
        Path(__file__).parent.resolve() / "./sql/get_order_information.sql"
    )

    @staticmethod
    def search_order(search: str):
        result = db_service.execute_query(
            connection_type=DatabaseConnection.ERP,
            sql_query=f"""--sql
                SELECT TOP 5 mo_no
                FROM (
                    SELECT DISTINCT mo_no, created
                    FROM wuerp_vnrd.dbo.ta_manufacturmst
                    WHERE mo_no LIKE '%{search}%'
                    AND cofactory_code = '{auth_context.get("factory_code")}'
                ) AS subquery
                ORDER BY created DESC
            """,
        )
        if result is None:
            return []
        return result

    @staticmethod
    def get_order_detail(params: dict):
        return db_service.execute_query(
            connection_type=DatabaseConnection.ERP,
            sql_query=db_service.get_raw_sql(OrderRepository.__sql_file_path),
            bind_values={"mo_no": params["mo_no"]},
        )
        # results = []
        # try:
        #     sql_statement = db_service.get_raw_sql(OrderRepository.__sql_file_path)
        #     connection = db_service.get_connection(DatabaseConnection.ERP)
        #     query = QSqlQuery(connection)
        #     query.prepare(sql_statement)
        #     query.bindValue(":mo_no", params["mo_no"])
        #     query.exec()
        #     while query.next():
        #         results.append(
        #             {
        #                 "shoestyle_codefactory": query.value("shoestyle_codefactory"),
        #                 "mo_no": query.value("mo_no"),
        #                 "mat_code": query.value("mat_code"),
        #                 "cust_shoestyle": query.value("cust_shoestyle"),
        #                 "mo_noseq": query.value("mo_noseq"),
        #                 "or_no": query.value("or_no"),
        #                 "or_custpo": query.value("or_custpo"),
        #                 "size_qty": query.value("size_qty"),
        #             }
        #         )

        # except Exception as e:
        #     logger.error(f"Error finding order detail: {e}")
        # finally:
        #     query.finish()
        #     return results
