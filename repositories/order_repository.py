from PyQt6.QtSql import *

from contexts.auth_context import auth_context
from database import DatabaseConnection, db_service
from helpers.logger import logger
from repositories.sql import GET_ORDER_INFORMATION_SQL


class OrderRepository:
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
            sql_query=GET_ORDER_INFORMATION_SQL,
            bind_values={"mo_no": params["mo_no"]},
        )
