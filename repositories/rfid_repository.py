import asyncio
from database import get_raw_sql
from PyQt6.QtSql import *
from helpers.logger import logger
import numpy as np
from events import sync_event_emitter, UserActionEvent
from contexts.combine_form_context import combine_form_context
from database import DATA_SOURCE_DL


class RFIDRepository:

    @staticmethod
    def check_if_epc_new(epcs: list[str]) -> bool:
        epcs_list_str = ",".join([f"'{epc.strip()}'" for epc in epcs])
        try:
            total_qty = None
            query = QSqlQuery(DATA_SOURCE_DL)
            query.prepare(
                f"""--sql;
                SELECT COUNT(DISTINCT EPC_Code) AS count
                    FROM DV_DATA_LAKE.dbo.dv_rfidmatchmst
                    WHERE EPC_Code IN ({epcs_list_str})
                 
            """
            )

            if not query.exec():
                raise Exception(query.lastError().text())

            if query.next():
                total_qty = query.value("count")
                logger.debug(total_qty)

            return total_qty == 0
        except Exception as e:
            logger.error(e)
        finally:
            query.finish()

    @staticmethod
    def get_recently_combined_epcs(epcs: list[str]) -> list[str]:
        """
        Check if the EPCs are recently combined
        """
        result = []
        epc_list_str = ",".join([f"'{epc.strip()}'" for epc in epcs])
        try:
            query = QSqlQuery(DATA_SOURCE_DL)
            query.prepare(
                f"""--sql
                    SELECT DISTINCT a.EPC_Code
                    FROM DV_DATA_LAKE.dbo.dv_RFIDrecordmst a
                    INNER JOIN DV_DATA_LAKE.dbo.dv_rfidmatchmst b
                    ON a.matchkeyid = b.keyid AND a.EPC_Code = b.EPC_Code
                    WHERE a.EPC_Code IN ({epc_list_str})
                        AND a.isactive = 'Y'
                        AND b.isactive = 'Y'
                        AND b.ri_cancel = 0
                """
            )
            query.exec()

            while query.next():
                result.append(query.value("EPC_Code"))

            return result

        except Exception as e:
            logger.error(f"Error: {e}")
            raise Exception(e)
        finally:
            query.finish()

    @staticmethod
    def get_lifecycle_ended_epcs(epcs: list[str]):
        """
        Check if the EPCs are still in the lifecycle, if not allow user to combine them
        """
        try:
            result = []

            query = QSqlQuery(DATA_SOURCE_DL)
            epc_params_str = ",".join([f"'{epc.strip()}'" for epc in epcs])
            query.prepare(
                f"""--sql
                    WITH datalist AS (
                        SELECT EPC_Code, matchkeyid 
                        FROM DV_DATA_LAKE.dbo.dv_RFIDrecordmst
                        WHERE EPC_Code IN ({epc_params_str})
                            AND stationNO LIKE '%P%103'
                        UNION ALL
                        SELECT EPC_Code, matchkeyid
                        FROM DV_DATA_LAKE.dbo.dv_RFIDrecordmst_backup_Daily
                        WHERE EPC_Code IN ({epc_params_str})
                            AND stationNO LIKE '%P%103'
                    )
                    SELECT DISTINCT a.EPC_Code FROM datalist a
                    INNER JOIN DV_DATA_LAKE.dbo.dv_rfidmatchmst b
                        ON a.matchkeyid = b.keyid AND a.EPC_Code = b.EPC_Code
                    WHERE b.ri_cancel = 0
                        AND DATEDIFF(DAY, CAST(GETDATE() AS DATE), CAST(b.ri_date AS DATE)) >= 3
                """
            )

            if not query.exec():
                raise Exception(query.lastError().text())

            while query.next():
                result.append(query.value("EPC_Code"))

            return result

        except Exception as e:
            logger.error(f"Error: {e}")
            raise Exception(e)
        finally:
            query.finish()

    @staticmethod
    def get_active_combinations(epcs: list[str]) -> list[dict[str, str]]:
        """
        Get combination history of an EPC
        """
        try:
            result = []

            query = QSqlQuery(DATA_SOURCE_DL)
            epc_params_str = ",".join([f"'{epc.strip()}'" for epc in epcs])

            query.prepare(
                f"""--sql
                     WITH datalist AS (
                        SELECT EPC_Code, stationNO, matchkeyid 
                        FROM DV_DATA_LAKE.dbo.dv_RFIDrecordmst
                        WHERE EPC_Code IN ({epc_params_str})
                        UNION ALL
                        SELECT EPC_Code, stationNO, matchkeyid
                        FROM DV_DATA_LAKE.dbo.dv_RFIDrecordmst_backup_Daily
                        WHERE EPC_Code IN ({epc_params_str})
                    )
                    SELECT DISTINCT a.EPC_Code, b.mo_no, b.size_numcode, b.ri_date, a.stationNO 
                    FROM datalist a
                    INNER JOIN DV_DATA_LAKE.dbo.dv_rfidmatchmst b
                        ON a.matchkeyid = b.keyid AND a.EPC_Code = b.EPC_Code
                    WHERE b.ri_cancel = 0
                """
            )

            if not query.exec():
                raise Exception(query.lastError().text())

            while query.next():
                result.append(
                    {
                        "EPC_Code": query.value("EPC_Code"),
                        "mo_no": query.value("mo_no"),
                        "size_numcode": query.value("size_numcode"),
                        "ri_date": query.value("ri_date"),
                        "stationNO": query.value("stationNO"),
                    }
                )

        except Exception as e:
            logger.error(f"Error: {e}")
            raise Exception(e)
        finally:
            query.finish()
            return result

    @staticmethod
    def reset_and_add_combinations(data: dict):
        query = QSqlQuery(DATA_SOURCE_DL)

        try:
            epc_params_str = ",".join([f"'{item['EPC_Code']}'" for item in data])

            insert_values = ",".join(
                map(
                    lambda item: f"""(
                    '{item['EPC_Code']}', 
                    '{item['mo_no']}',
                    '{item['mo_noseq']}',
                    '{item['mat_code']}',
                    '{item['or_no']}',
                    '{item['or_custpo']}',
                    '{item['shoestyle_codefactory']}',
                    '{item['cust_shoestyle']}',
                    '{item['size_numcode']}',
                    '{item['size_code']}',
                    {item['size_qty']},
                    '{item['factory_code_orders']}',
                    '{item['factory_name_orders']}',
                    '{item['factory_code_produce']}',
                    '{item['factory_name_produce']}',
                    GETDATE(),
                    {item['ri_cancel']},
                    '{item['ri_type']}',
                    '{item['ri_foot']}',
                    '{item['sole_tag']}',
                    {item['sole_tag_rate']},
                    {item['sole_tag_round']},
                    '{item['user_code_created']}',
                    '{item['user_name_created']}',
                    '{item['dept_code']}',
                    '{item['dept_name']}',
                    '{item['isactive']}',
                    '{item['remark']}'
                )""",
                    data,
                )
            )

            DATA_SOURCE_DL.transaction()

            query.prepare(
                f"""--sql
                    -- Cancel old records
                    UPDATE DV_DATA_LAKE.dbo.dv_rfidmatchmst
                    SET ri_cancel = 1, 
                        ri_reason_cancel = 'EPC lifecycle ended', 
                        ri_cancel_date = GETDATE(),
                        user_code_updated = '{combine_form_context["user_code_updated"]}',
                        user_name_updated = '{combine_form_context["user_name_updated"]}'
                    WHERE EPC_Code IN ({epc_params_str});    
                    -- Insert new records    
                    INSERT INTO DV_DATA_LAKE.dbo.dv_rfidmatchmst (
                            EPC_Code, mo_no, mo_noseq, mat_code,  or_no, or_custpo, 
                            shoestyle_codefactory, cust_shoestyle, size_numcode, size_code, size_qty,
                            factory_code_orders, factory_name_orders, factory_code_produce, factory_name_produce, 
                            ri_date, ri_cancel, ri_type, ri_foot, 
                            sole_tag, sole_tag_rate, sole_tag_round, 
                            user_code_created, user_name_created, 
                            dept_code, dept_name,
                            isactive, remark
                        )
                        VALUES {insert_values}   
                """
            )
            if not query.exec():
                raise Exception(query.lastError().text())

            DATA_SOURCE_DL.commit()

            logger.info("--------------- Insert match successfully ---------------")

            return query.numRowsAffected()

        except Exception as e:
            DATA_SOURCE_DL.rollback()
            logger.error(f"Error: {e}")
            raise Exception(e)
        finally:
            query.finish()
