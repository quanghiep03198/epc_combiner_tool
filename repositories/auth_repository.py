from PyQt6.QtSql import QSqlQuery
from database import DATA_SOURCE_SYSCLOUD
from helpers.logger import logger

from constants import FactoryNames, StatusCode


class AuthRepository:
    @staticmethod
    def __init__(self, db):
        self.db = db

    @staticmethod
    def find_user(username: str):
        try:
            user: dict[str, str | None] = {
                "id": None,
                "employee_code": None,
                "employee_name": None,
                "user_code": None,
                "password": None,
            }

            query = QSqlQuery(DATA_SOURCE_SYSCLOUD)

            query.prepare(
                f"""--sql
                SELECT u.keyid, u.user_code, u.user_password, e.employee_code, e.employee_name
                FROM syscloud_vn.dbo.ts_user u
                INNER JOIN syscloud_vn.dbo.ts_employee e ON u.employee_code = e.employee_code
                WHERE u.user_code = :username
                """
            )

            query.bindValue(":username", username)

            if not query.exec():
                raise Exception(
                    {
                        "message": query.lastError().text(),
                        "status": StatusCode.INTERNAL_SERVER_ERROR.value,
                    }
                )

            if query.next():
                user.update(id=query.value("keyid"))
                user.update(user_code=query.value("user_code"))
                user.update(employee_code=query.value("employee_code"))
                user.update(employee_name=query.value("employee_name"))
                user.update(password=query.value("user_password"))

            return user
        finally:
            query.finish()

    @staticmethod
    def get_factories(user_id: int | str):
        result = []

        query = QSqlQuery(DATA_SOURCE_SYSCLOUD)

        query.prepare(
            f"""--sql
            SELECT DISTINCT f.factory_code, f.factory_extcode
            FROM syscloud_vn.dbo.ts_user u
            INNER JOIN syscloud_vn.dbo.ts_employee e ON e.employee_code = u.employee_code
            INNER JOIN syscloud_vn.dbo.ts_employeedept ed ON ed.employee_code = e.employee_code
            INNER JOIN syscloud_vn.dbo.ts_dept d ON d.dept_code = ed.dept_code
            INNER JOIN syscloud_vn.dbo.ts_factory f ON f.factory_code = d.company_code
            WHERE u.keyid = :id AND f.factory_extcode <> 'GL5'
            ORDER BY f.factory_extcode ASC
        """
        )

        query.bindValue(":id", user_id)

        if not query.exec():
            logger.error(
                {
                    "message": query.lastError().text(),
                    "status": StatusCode.INTERNAL_SERVER_ERROR.value,
                }
            )

        while query.next():
            factory_code = query.value("factory_code")
            result.append(
                {
                    "factory_code": factory_code,
                    "factory_name": FactoryNames[factory_code].value,
                }
            )

        return result
