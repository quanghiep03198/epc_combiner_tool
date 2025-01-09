DECLARE @concatenated_codes NVARCHAR(MAX);

SELECT @concatenated_codes = STRING_AGG(EPC_Code, ',')
FROM dv_rfidmatchmst
WHERE remark LIKE '%quanghiep03198';

EXEC SP_UpsertEpcRecord @concatenated_codes, 'VA1_PA103';