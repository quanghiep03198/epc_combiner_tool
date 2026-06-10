from PyQt6.QtSql import QSqlQuery

from constants import FactoryNames, StatusCode
from database import DatabaseConnection, db_service
from helpers.logger import logger


class AuthRepository:

    @staticmethod
    def find_user(username: str):
        result = db_service.execute_query(
            connection_type=DatabaseConnection.SYSCLOUD,
            sql_query="""--sql
                SELECT u.keyid AS id, u.user_code, u.user_password AS password, e.employee_code, e.employee_name
                FROM syscloud_vn.dbo.ts_user u
                INNER JOIN syscloud_vn.dbo.ts_employee e ON u.employee_code = e.employee_code
                WHERE u.user_code = :username
            """,
            bind_values={"username": username},
        )

        if result is None or len(result) == 0:
            return {
                "id": None,
                "employee_code": None,
                "employee_name": None,
                "user_code": None,
                "password": None,
            }
        return result[0]

    @staticmethod
    def get_factories(user_id: int | str):
        result = db_service.execute_query(
            connection_type=DatabaseConnection.SYSCLOUD,
            sql_query="""--sql
                SELECT DISTINCT f.factory_code, f.factory_extcode
                FROM syscloud_vn.dbo.ts_user u
                INNER JOIN syscloud_vn.dbo.ts_employee e ON e.employee_code = u.employee_code
                INNER JOIN syscloud_vn.dbo.ts_employeedept ed ON ed.employee_code = e.employee_code
                INNER JOIN syscloud_vn.dbo.ts_dept d ON d.dept_code = ed.dept_code
                INNER JOIN syscloud_vn.dbo.ts_factory f ON f.factory_code = d.company_code
                WHERE u.keyid = :id AND f.factory_code IN ('VA1','VB1','VB2','CA1')
                ORDER BY f.factory_extcode ASC
            """,
            bind_values={"id": user_id},
        )

        if result is None or not isinstance(result, list):
            return []

        # Map result to desired format
        return list(
            map(
                lambda row: {
                    "factory_code": row["factory_code"],
                    "factory_name": FactoryNames[row["factory_code"]].value,
                },
                result,
            )
        )
