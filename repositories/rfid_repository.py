from PyQt6.QtSql import *
from helpers.logger import logger
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
                        AND ri_cancel = 0
                        AND isactive = 'Y' 
                 
            """
            )

            if not query.exec():
                raise Exception(query.lastError().text())

            if query.next():
                total_qty = query.value("count")

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
        try:
            query = QSqlQuery(DATA_SOURCE_DL)
            query.prepare(
                f"""--sql
                    WITH datalist AS (
                        SELECT DISTINCT EPC_Code, matchkeyid, mo_no, isactive
                        FROM DV_DATA_LAKE.dbo.dv_RFIDrecordmst
                        UNION ALL 
                        SELECT EPC_Code, matchkeyid, mo_no, isactive 
                        FROM DV_DATA_LAKE.dbo.dv_RFIDrecordmst_backup_Daily
                    )
                    SELECT DISTINCT a.EPC_Code FROM datalist a
                    INNER JOIN DV_DATA_LAKE.dbo.dv_rfidmatchmst b
                    ON a.matchkeyid = b.keyid 
                        AND a.EPC_Code = b.EPC_Code
                        AND a.mo_no = b.mo_no
                    WHERE 
                        a.EPC_Code IN (
                            SELECT value AS EPC_Code 
                            FROM STRING_SPLIT(CAST(:epc_list AS NVARCHAR(MAX)), ',')
                        )
                        AND a.isactive = 'Y'
                        AND b.isactive = 'Y'
                        AND b.ri_cancel = 0
                """
            )

            query.bindValue(":epc_list", ",".join(epcs))

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
        result = []
        try:

            query = QSqlQuery(DATA_SOURCE_DL)
            query.prepare(
                f"""--sql
                    WITH datalist AS (
                        SELECT EPC_Code, mo_no, stationNO, matchkeyid 
                        FROM DV_DATA_LAKE.dbo.dv_RFIDrecordmst
                        UNION ALL
                        SELECT EPC_Code, mo_no, stationNO, matchkeyid
                        FROM DV_DATA_LAKE.dbo.dv_RFIDrecordmst_backup_Daily
                    )
                    SELECT DISTINCT a.EPC_Code FROM datalist a
                    INNER JOIN DV_DATA_LAKE.dbo.dv_rfidmatchmst b
                        ON a.matchkeyid = b.keyid 
                        AND a.EPC_Code = b.EPC_Code
                        AND a.mo_no = b.mo_no
                    WHERE 
                        a.EPC_Code IN (
                            SELECT value AS EPC_Code 
                            FROM STRING_SPLIT(CAST(:epc_list AS NVARCHAR(MAX)), ',')
                        )
                        AND b.ri_cancel = 0
                        AND a.stationNO LIKE '%P%103'
                        AND DATEDIFF(DAY, CAST(b.ri_date AS DATE), CAST(GETDATE() AS DATE)) >= 3
                """
            )

            query.bindValue(":epc_list", ",".join(epcs))

            if not query.exec():
                raise Exception(query.lastError().text())

            while query.next():
                result.append(query.value("EPC_Code"))
            return result
        except Exception as e:
            logger.error(e)
        finally:
            query.finish()
            return result

    @staticmethod
    def get_ng_epc_detail(epcs: list[str]) -> list[dict[str, str]]:
        """
        Get combination history of an EPC
        """
        result = []
        try:

            query = QSqlQuery(DATA_SOURCE_DL)

            query.prepare(
                f"""--sql
                    WITH datalist AS (
                    SELECT EPC_Code, stationNO, matchkeyid 
                    FROM DV_DATA_LAKE.dbo.dv_RFIDrecordmst
                    UNION ALL
                    SELECT EPC_Code, stationNO, matchkeyid
                    FROM DV_DATA_LAKE.dbo.dv_RFIDrecordmst_backup_Daily
                )
                SELECT DISTINCT a.keyid, a.EPC_Code, a.mo_no, a.size_numcode, a.ri_date, b.stationNO
                FROM DV_DATA_LAKE.dbo.dv_rfidmatchmst a
                LEFT JOIN datalist b
                    ON a.keyid = b.matchkeyid AND a.EPC_Code = b.EPC_Code
                WHERE a.EPC_Code IN (
                        SELECT value AS EPC_Code 
                        FROM STRING_SPLIT(CAST(:epc_list AS NVARCHAR(MAX)), ',')
                    )
                    AND a.ri_cancel = 0
                """
            )

            query.bindValue(":epc_list", ",".join(epcs))

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

            return query.numRowsAffected()

        except Exception as e:
            DATA_SOURCE_DL.rollback()
            logger.error(f"Error: {e}")
            raise Exception(e)
        finally:
            query.finish()
