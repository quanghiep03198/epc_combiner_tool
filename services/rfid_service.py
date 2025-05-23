from repositories.rfid_repository import RFIDRepository
from helpers.logger import logger
from PyQt6.QtSql import *
import numpy
from database import DATA_SOURCE_DL
from contexts.auth_context import auth_context
from i18n import I18nService


class RFIDService:
    @staticmethod
    def reset_and_add_combinations(data: dict) -> int | None:
        """
        Cancel the previous combinations and add new the ones
        """
        try:
            return RFIDRepository.reset_and_add_combinations(data)
        except Exception as e:
            raise Exception(e.args[0])

    @staticmethod
    def get_ng_epc_detail(epcs: list[str]) -> list[dict[str, str]]:
        """
        Deprecated

        Get the EPCs that are not in the lifecycle
        """

        return RFIDRepository.get_ng_epc_detail(epcs)

    @staticmethod
    def force_end_lifecycle(payload: dict) -> int:
        """
        Deprecated

        Force end the lifecycle of the EPCs
        """

        epcs = payload["epcs"]
        mo_no = payload["mo_no"]
        size_code = payload["size_code"]
        fallback_station_no = "%s_%s" % (auth_context.get("factory_code"), "PA103")

        query = QSqlQuery(DATA_SOURCE_DL)
        try:
            query.prepare(
                """--sql
                UPDATE DV_DATA_LAKE.dbo.dv_RFIDrecordmst
                SET stationNO = (
                    SELECT COALESCE(
                    -- find stationNO by both mo_no and size_code
                    (
                        SELECT TOP 1 stationNO
                        FROM DV_DATA_LAKE.dbo.dv_RFIDrecordmst 
                        WHERE mo_no = :mo_no
                            AND size_code = :size_code
                            AND stationNO LIKE '%P%103'
                        ORDER BY record_time DESC
                    ), 
                    -- else if find stationNO by only mo_no
                    (
                        SELECT TOP 1 stationNO
                        FROM DV_DATA_LAKE.dbo.dv_RFIDrecordmst 
                        WHERE mo_no = :mo_no
                            AND stationNO LIKE '%P%103'
                        ORDER BY record_time DESC
                    ), 
                    -- else use the fallback stationNO
                    :fallback_station_no
                    ) AS stationNO
                ),
                user_code_updated = :user_code_updated,
                user_name_updated = :user_name_updated,
                remark = :remark
                WHERE matchkeyid IN (
                    SELECT keyid as matchkeyid 
                    FROM DV_DATA_LAKE.dbo.dv_rfidmatchmst 
                    WHERE EPC_Code IN ( 
                        SELECT value AS EPC_Code 
                        FROM STRING_SPLIT(CAST(:epc_list AS NVARCHAR(MAX)), ',')
                    )
                )
            """
            )
            query.bindValue(":mo_no", mo_no)
            query.bindValue(":size_code", size_code)
            query.bindValue(":fallback_station_no", fallback_station_no)
            query.bindValue(":epc_list", ",".join(epcs))
            query.bindValue(":user_code_updated", auth_context.get("user_code"))
            query.bindValue(":user_name_updated", auth_context.get("employee_name"))
            query.bindValue(
                ":remark", f"Compensated by {auth_context.get('user_code')}"
            )

            if not query.exec():
                raise Exception(query.lastError().text())

            result = query.numRowsAffected()
            return result
        except Exception as e:
            logger.error(e)
            raise Exception(e)
        finally:
            query.finish()
            return 0

    @staticmethod
    def force_cancel(epcs: list[str]) -> int:
        """
        Deprecated

        Force cancel the EPCs
        """

        query = QSqlQuery(DATA_SOURCE_DL)
        try:
            query.prepare(
                """--sql
                UPDATE DV_DATA_LAKE.dbo.dv_rfidmatchmst
                SET ri_cancel = 1, isactive = 'N'
                WHERE EPC_Code IN (
                    SELECT value AS EPC_Code 
                    FROM STRING_SPLIT(CAST(:epc_list AS NVARCHAR(MAX)), ',')
                )
            """
            )
            query.bindValue(":epc_list", ",".join(epcs))

            if not query.exec():
                raise Exception(query.lastError().text())

            return query.numRowsAffected()
        except Exception as e:
            logger.error(e)
            raise Exception(e)
        finally:
            query.finish()
            return 0
