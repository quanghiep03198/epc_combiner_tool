from PyQt6.QtSql import *
from helpers.logger import logger
from contexts.combine_form_context import combine_form_context
from database import DATA_SOURCE_DL
from contexts.auth_context import auth_context
from helpers.disutils import strtobool


class RFIDRepository:
    @staticmethod
    def check_reasonable_combination(data: dict) -> list[dict]:
        result: list[dict] = []
        try:
            query = QSqlQuery(DATA_SOURCE_DL)
            epc_list = ",".join([f"'{item['EPC_Code']}'" for item in data])
            query.prepare(
                f"""--sql
                SELECT EPC_Code, 
                    CASE WHEN CAST(ri_date AS DATE) <= CAST(DATEADD(DAY, -2, GETDATE()) AS DATE) 
                    THEN 't' ELSE 'f' END AS recombinable
                FROM DV_DATA_LAKE.dbo.dv_rfidmatchmst
                WHERE EPC_Code IN ({epc_list})
                    AND ri_cancel = 0
                """
            )
            query.exec()
            while query.next():
                result.append(
                    {
                        "EPC_Code": query.value("EPC_Code"),
                        "recombinable": strtobool(query.value("recombinable")),
                    }
                )
            return result
        except:
            raise Exception("Error checking reasonable combination")

    @staticmethod
    def reset_and_add_combinations(data: dict):
        query = QSqlQuery(DATA_SOURCE_DL)
        try:
            epc_params_str = ",".join([f"'{item['EPC_Code']}'" for item in data])
            fallback_station_no = "%s_%s" % (auth_context.get("factory_code"), "PA103")

            insert_values = ",".join(
                map(
                    lambda item: f"""(
                    '{str(item['EPC_Code']).replace("'", "''")}', 
                    '{str(item['mo_no']).replace("'", "''")}',
                    '{str(item['mo_noseq']).replace("'", "''")}',
                    '{str(item['mat_code']).replace("'", "''")}',
                    '{str(item['or_no']).replace("'", "''")}',
                    '{str(item['or_custpo']).replace("'", "''")}',
                    '{str(item['shoestyle_codefactory']).replace("'", "''")}',
                    '{str(item['cust_shoestyle']).replace("'", "''")}',
                    '{str(item['size_numcode']).replace("'", "''")}',
                    '{str(item['size_code']).replace("'", "''")}',
                    {item['size_qty']},
                    '{str(item['factory_code_orders']).replace("'", "''")}',
                    '{str(item['factory_name_orders']).replace("'", "''")}',
                    '{str(item['factory_code_produce']).replace("'", "''")}',
                    '{str(item['factory_name_produce']).replace("'", "''")}',
                    GETDATE(),
                    {item['ri_cancel']},
                    '{str(item['ri_type']).replace("'", "''")}',
                    '{str(item['ri_foot']).replace("'", "''")}',
                    '{str(item['sole_tag']).replace("'", "''")}',
                    {item['sole_tag_rate']},
                    {item['sole_tag_round']},
                    '{str(item['user_code_created']).replace("'", "''")}',
                    '{str(item['user_name_created']).replace("'", "''")}',
                    '{str(item['dept_code']).replace("'", "''")}',
                    '{str(item['dept_name']).replace("'", "''")}',
                    '{str(item['isactive']).replace("'", "''")}',
                    '{str(item['remark']).replace("'", "''")}'
                )""",
                    data,
                )
            )

            # Force end EPC's lifecycle
            query.prepare(
                f"""-- sql
                UPDATE DV_DATA_LAKE.dbo.dv_RFIDrecordmst
                SET stationNO = (
                    SELECT COALESCE(
                        -- find stationNO by both "mo_no" and "size_code"
                        (
                            SELECT TOP 1 a.stationNO
                            FROM DV_DATA_LAKE.dbo.dv_RFIDrecordmst a, DV_DATA_LAKE.dbo.dv_RFIDrecordmst b 
                            WHERE b.stationNO NOT LIKE '%P%103' 
                            AND a.mo_no = b.mo_no  
                            AND a.size_code = b.size_code
                            AND a.stationNO <> b.stationNO
                            AND a.EPC_Code <> b.EPC_Code 
                            AND b.EPC_Code IN ({epc_params_str})
                            ORDER BY a.record_time DESC
                        ), 
                        -- else use the fallback stationNO
                        '{fallback_station_no}'
                        ) AS stationNO
                    ),              
                    user_code_updated = '{combine_form_context.get("user_code_updated")}',
                    user_name_updated = '{combine_form_context.get("user_name_updated")}',
                    record_time = DATEADD(DAY, -7, GETDATE()),
                    remark = 'Forced lifecycle end by {combine_form_context.get("user_name_updated")}'
                WHERE 
                    matchkeyid IN (
                        SELECT a.keyid as matchkeyid 
                        FROM DV_DATA_LAKE.dbo.dv_rfidmatchmst a
                        INNER JOIN DV_DATA_LAKE.dbo.dv_RFIDrecordmst b
                            ON a.EPC_Code = b.EPC_Code
                            AND a.keyid = b.matchkeyid
                        WHERE a.EPC_Code IN ({epc_params_str})
                            AND a.ri_cancel = 0  
                            AND b.stationNO NOT LIKE '%P%103'
                    )
                ;
                """
            )

            if not query.exec():
                raise Exception(query.lastError().text())

            # Cancel old records
            query.prepare(
                f"""--sql          
                UPDATE DV_DATA_LAKE.dbo.dv_rfidmatchmst
                SET ri_cancel = 1, 
                    ri_reason_cancel = 'EPC lifecycle ended', 
                    ri_cancel_date = GETDATE(),
                    user_code_updated = '{combine_form_context.get("user_code_updated")}',
                    user_name_updated = '{combine_form_context.get("user_name_updated")}'
                WHERE EPC_Code IN ({epc_params_str})
                    AND ri_cancel = 0
                    AND sole_tag = 'A'
                ;
                """
            )

            if not query.exec():
                raise Exception(query.lastError().text())

            # Insert new records
            query.prepare(
                f"""--sql
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
            ;
            """
            )

            if not query.exec():
                raise Exception(query.lastError().text())

            DATA_SOURCE_DL.commit()
            return query.numRowsAffected()
        except Exception as e:
            DATA_SOURCE_DL.rollback()
            logger.error(f"Error in RFIDRepository: {e}")
            raise Exception(e)
        finally:
            query.finish()
