DECLARE @JsonData NVARCHAR(MAX) = :json_data;

INSERT INTO DV_DATA_LAKE.dbo.dv_rfidmatchmst (
    EPC_Code, mo_no, mo_noseq, mat_code, or_no, or_custpo, 
    shoestyle_codefactory, cust_shoestyle, size_numcode, size_code, size_qty,
    factory_code_orders, factory_name_orders, factory_code_produce, factory_name_produce, 
    ri_date, ri_cancel, ri_type, ri_foot, 
    sole_tag, sole_tag_rate, sole_tag_round, 
    user_code_created, user_name_created, 
    dept_code, dept_name,
    isactive, remark
)
SELECT 
    JSON_VALUE(value, '$.EPC_Code') AS EPC_Code,
    JSON_VALUE(value, '$.mo_no') AS mo_no,
    JSON_VALUE(value, '$.mo_noseq') AS mo_noseq,
    JSON_VALUE(value, '$.mat_code') AS mat_code,
    JSON_VALUE(value, '$.or_no') AS or_no,
    JSON_VALUE(value, '$.or_custpo') AS or_custpo,
    JSON_VALUE(value, '$.shoestyle_codefactory') AS shoestyle_codefactory,
    JSON_VALUE(value, '$.cust_shoestyle') AS cust_shoestyle,
    JSON_VALUE(value, '$.size_numcode') AS size_numcode,
    JSON_VALUE(value, '$.size_code') AS size_code,
    CAST(JSON_VALUE(value, '$.size_qty') AS INT) AS size_qty,
    JSON_VALUE(value, '$.factory_code_orders') AS factory_code_orders,
    JSON_VALUE(value, '$.factory_name_orders') AS factory_name_orders,
    JSON_VALUE(value, '$.factory_code_produce') AS factory_code_produce,
    JSON_VALUE(value, '$.factory_name_produce') AS factory_name_produce,
    GETDATE() AS ri_date,
    CAST(JSON_VALUE(value, '$.ri_cancel') AS INT) AS ri_cancel,
    JSON_VALUE(value, '$.ri_type') AS ri_type,
    JSON_VALUE(value, '$.ri_foot') AS ri_foot,
    JSON_VALUE(value, '$.sole_tag') AS sole_tag,
    CAST(JSON_VALUE(value, '$.sole_tag_rate') AS FLOAT) AS sole_tag_rate,
    CAST(JSON_VALUE(value, '$.sole_tag_round') AS FLOAT) AS sole_tag_round,
    JSON_VALUE(value, '$.user_code_created') AS user_code_created,
    JSON_VALUE(value, '$.user_name_created') AS user_name_created,
    JSON_VALUE(value, '$.dept_code') AS dept_code,
    JSON_VALUE(value, '$.dept_name') AS dept_name,
    JSON_VALUE(value, '$.isactive') AS isactive,
    JSON_VALUE(value, '$.remark') AS remark
FROM OPENJSON(@JsonData)