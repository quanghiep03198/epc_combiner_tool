DECLARE @PendingCombineEpcs NVARCHAR(MAX) = :pending_combine_epcs;
DECLARE @User NVARCHAR(MAX) = :username;

UPDATE DV_DATA_LAKE.dbo.dv_rfidmatchmst
SET ri_cancel = 1, 
    ri_reason_cancel = 'EPC lifecycle ended', 
    ri_cancel_date = GETDATE(),
    user_code_updated = @User,
    user_name_updated = @User
WHERE EPC_Code IN (SELECT value FROM STRING_SPLIT(@PendingCombineEpcs, ','))
    AND ri_cancel = 0
    AND sole_tag = 'A'
;