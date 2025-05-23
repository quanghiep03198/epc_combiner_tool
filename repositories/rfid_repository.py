from PyQt6.QtSql import *
from helpers.logger import logger
from contexts.combine_form_context import combine_form_context
from database import DATA_SOURCE_DL
from contexts.auth_context import auth_context


class RFIDRepository:
    @staticmethod
    def reset_and_add_combinations(data: dict):
        query = QSqlQuery(DATA_SOURCE_DL)
        try:
            epc_params_str = ",".join([f"'{item['EPC_Code']}'" for item in data])
            fallback_station_no = "%s_%s" % (auth_context.get("factory_code"), "PA103")

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

            query.prepare(
                f"""-- sql
                    -- Force EPC's lifecycle end
                    UPDATE DV_DATA_LAKE.dbo.dv_RFIDrecordmst
                    SET stationNO = (
                        SELECT COALESCE(
                        -- find stationNO by both mo_no and size_code
                            (
                                SELECT TOP 1 stationNO
                                FROM DV_DATA_LAKE.dbo.dv_RFIDrecordmst 
                                WHERE mo_no = '{combine_form_context.get('mo_no')}'
                                    AND size_code = '{combine_form_context.get('size_code')}'
                                    AND stationNO LIKE '%P%103'
                                ORDER BY record_time DESC
                            ), 
                            -- else if find stationNO by only mo_no
                            (
                                SELECT TOP 1 stationNO
                                FROM DV_DATA_LAKE.dbo.dv_RFIDrecordmst 
                                WHERE mo_no = '{combine_form_context.get('mo_no')}'
                                    AND stationNO LIKE '%P%103'
                                ORDER BY record_time DESC
                            ), 
                            -- else use the fallback stationNO
                            '{fallback_station_no}'
                            ) AS stationNO
                        ),
                        user_code_updated = '{combine_form_context.get("user_code_updated")}',
                        user_name_updated = '{combine_form_context.get("user_name_updated")}',
                        record_time = DATEADD(DAY, -7, GETDATE()),
                        remark = 'Forced lifecycle end by {combine_form_context.get("user_name_updated")}'
                    WHERE matchkeyid IN (
                            SELECT a.keyid as matchkeyid 
                            FROM DV_DATA_LAKE.dbo.dv_rfidmatchmst a
                            LEFT JOIN DV_DATA_LAKE.dbo.dv_RFIDrecordmst b
                                ON a.EPC_Code = b.EPC_Code
                                AND a.keyid = b.matchkeyid
                            WHERE a.EPC_Code IN ({epc_params_str})
                                AND a.ri_cancel = 0  
                                AND b.stationNO LIKE '%P%103'
                        )
                    ;

                    -- Cancel old records
                    UPDATE DV_DATA_LAKE.dbo.dv_rfidmatchmst
                    SET ri_cancel = 1, 
                        ri_reason_cancel = 'EPC lifecycle ended', 
                        ri_cancel_date = GETDATE(),
                        user_code_updated = '{combine_form_context.get("user_code_updated")}',
                        user_name_updated = '{combine_form_context.get("user_name_updated")}'
                    WHERE EPC_Code IN ({epc_params_str})
                        AND ri_cancel = 0
                        AND isactive = 'Y';   

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
