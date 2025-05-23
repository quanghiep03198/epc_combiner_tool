USE DV_DATA_LAKE;

SELECT *
FROM DV_DATA_LAKE.dbo.dv_rfidmatchmst
WHERE EPC_Code IN ('E28068940000502B3A04F88D')
   AND ri_cancel = 0
   AND sole_tag = 'A'
   AND isactive = 'Y' 
-- AND DATEDIFF(DAY, CAST(GETDATE() AS DATE), CAST(b.ri_date AS DATE)) >= 3