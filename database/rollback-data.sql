-- SELECT COUNT(EPC_Code) AS count
--                 FROM dv_rfidmatchmst a
--                 WHERE EXISTS (
--                     SELECT b.matchkeyid
--                     FROM dv_RFIDrecordmst b
--                     WHERE EPC_Code IN ('E28069150000401D2B969922','E28069150000501D2B9408EC','E28069150000501D2B93FCEC','E28069150000501D2B94F4C7')
--                     AND b.matchkeyid = a.keyid
--                     AND b.isactive = 'Y'
--                 )
--                 AND a.isactive = 'Y';



BEGIN TRY
    BEGIN TRANSACTION

    DELETE FROM DV_DATA_LAKE.dbo.dv_RFIDrecordmst WHERE matchkeyid IN (
        SELECT keyid AS matchkeyid 
        FROM DV_DATA_LAKE.dbo.dv_rfidmatchmst 
        WHERE remark LIKE '%quanghiep03198'
    )

    DELETE FROM DV_DATA_LAKE.dbo.dv_rfidmatchmst WHERE remark LIKE '%quanghiep03198'

    COMMIT TRANSACTION
END TRY
BEGIN CATCH
    ROLLBACK TRANSACTION
    THROW
END CATCH

