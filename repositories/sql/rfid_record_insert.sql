use DV_DATA_LAKE;


DECLARE @concatenated_codes NVARCHAR(MAX),
@user_code NVARCHAR(255) = '';

-- Add to RFID records
SELECT @concatenated_codes = STRING_AGG(EPC_Code, ',')
FROM DV_DATA_LAKE.dbo.dv_rfidmatchmst a
WHERE EPC_Code IN (
   SELECT  EPC_Code
   FROM DV_DATA_LAKE.dbo.dv_rfidmatchmst a
   WHERE user_code_created = @user_code
)

EXEC SP_UpsertEpcRecord @concatenated_codes, 'VA1_IH101';

SELECT * FROM dv_RFIDRecordmst
WHERE EPC_Code IN (
   SELECT EPC_Code
   FROM DV_DATA_LAKE.dbo.dv_rfidmatchmst a
   WHERE user_code_created = @user_code
)
ORDER BY size_code ASC;

-- Update the ri_date and created fields for records created by 'quanghiep'
UPDATE dv_rfidmatchmst
SET ri_date = DATEADD(DAY, -7, ri_date),
created = DATEADD(DAY, -7, created)
WHERE user_code_created = @user_code
;






