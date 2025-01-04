import asyncio
from database import get_raw_sql
from PyQt6.QtSql import *
from helpers.logger import logger


class RFIDRepository:
    def __init__(self, data_source_dl: QSqlDatabase):
        self.data_source_dl = data_source_dl

    async def check_epc_lifecycle_end(self, epcs: list):
        """
        Check if the EPCs are still in the lifecycle, if not allow user to combine them
        """
        try:
            result = []

            query = QSqlQuery(self.data_source_dl)
            epc_params_str = ",".join([f"'{epc}'" for epc in epcs])
            query.prepare(
                f"""--sql
                    WITH datalist AS (
                        SELECT EPC_Code 
                        FROM dv_RFIDrecordmst
                        WHERE EPC_Code IN ({epc_params_str})
                            AND stationNO LIKE '%P%103'
                        UNION ALL
                        SELECT EPC_Code
                        FROM dv_RFIDrecordmst_backup_Daily
                        WHERE EPC_Code IN ({epc_params_str})
                            AND stationNO LIKE '%P%103'
                    )
                    SELECT d.EPC_Code FROM datalist a
                    LEFT JOIN dv_rfidmatchmst b
                        ON a.EPC_Code = b.EPC_Code
                    WHERE DATEDIFF(DAY, CAST(GETDATE() AS DATE), CAST(b.ri_date AS DATE)) >= 3
                """
            )
            query.exec()

            while query.next():
                result.append(query.value("EPC_Code"))

            return result

        except Exception as e:
            logger.error(f"Error: {e}")

        finally:
            query.finish()

    def insert_match(self, data: dict):
        query = QSqlQuery(self.data_source_dl)

        epc_params_str = ",".join([f"'{item['EPC_Code']}'" for item in data])
        logger.debug(epc_params_str)

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
                '{item['dept_code']}',
                '{item['dept_name']}',
                '{item['isactive']}',
                '{item['remark']}'
            )""",
                data,
            )
        )

        try:
            self.data_source_dl.transaction()

            query.prepare(
                f"""--sql
                    -- Cancel old record
                    UPDATE dv_rfidmatchmst
                    SET ri_cancel = 1, ri_reason_cancel = 'Phối lại', ri_cancel_date = GETDATE()
                    WHERE EPC_Code IN ({epc_params_str});    
                    -- Insert new record       
                    INSERT INTO dv_rfidmatchmst (
                            EPC_Code, mo_no, mo_noseq, mat_code,  or_no, or_custpo, 
                            shoestyle_codefactory, cust_shoestyle, size_numcode, size_code, size_qty,
                            factory_code_orders, factory_name_orders, factory_code_produce, factory_name_produce, 
                            ri_date, ri_cancel, ri_type, ri_foot, 
                            sole_tag, sole_tag_rate, sole_tag_round, 
                            dept_code, dept_name, 
                            isactive, remark
                        )
                        VALUES {insert_values}   
                """
            )
            if not query.exec():
                raise Exception(f"Execution failed: {query.lastError().text()}")

            self.data_source_dl.commit()
            logger.info("Insert match successfully")
            return query.numRowsAffected()
        except Exception as e:
            logger.error(f"Error: {e}")
            self.data_source_dl.rollback()
