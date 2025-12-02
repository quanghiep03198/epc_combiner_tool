DECLARE @JsonEpcCodes NVARCHAR(MAX) = :json_epcs_codes;
DECLARE @StationNO NVARCHAR(30) = :station_no;
DECLARE @TargetStationNO NVARCHAR(30) = :target_station_no;
DECLARE @RecordTime DATETIME = :record_time;
DECLARE @FactoryCode NVARCHAR(5) = :factory_code;
DECLARE @Username NVARCHAR(100) = :username; -- Or replace with actual username variable
DECLARE @InoutboundType NVARCHAR(1) = :inoutbound_type; -- Assuming 'A' for inbound, 'B' for outbound

MERGE INTO DV_DATA_LAKE.dbo.dv_RFIDrecordmst AS target
USING (
	SELECT keyid, 
		EPC_Code, 
		mo_no, 
		size_numcode AS size_code
	FROM DV_DATA_LAKE.dbo.dv_rfidmatchmst
	WHERE 
		ri_cancel = 0 
		AND ri_type = 'D'
      AND EPC_Code IN (
         SELECT value AS EPC_Code FROM OPENJSON(@JsonEpcCodes)
      )
) AS source
ON target.matchkeyid = source.keyid 
   AND target.EPC_Code = source.EPC_Code
   AND target.mo_no = source.mo_no
   AND target.size_code = source.size_code
   AND target.FC_server_code = @FactoryCode
	AND target.stationNO = @StationNO
	AND target.inoutbound_type = @InoutboundType
WHEN MATCHED THEN 
	UPDATE SET 
		target.rfid_status = 'A', -- Update rfid status
		target.inoutbound_type = @InoutboundType,
		target.record_time = ISNULL(@RecordTime, DATEADD(DAY, -7, GETDATE())),
		target.user_code_updated = @Username,
		target.user_name_updated = @Username,
		target.remark = 'Trace history at station ' + @TargetStationNO
WHEN NOT MATCHED THEN 
INSERT (
	matchkeyid, 
	EPC_Code, 
	mo_no, 
	size_code, 
	FC_server_code,
	stationNO,
   rfid_status,
	inoutbound_type, 
	record_time, 
	user_code_created, 
	user_name_created, 
   remark
)
VALUES (
	source.keyid, 
	source.EPC_Code, 
	source.mo_no, 
	source.size_code, 
	@FactoryCode,
	@StationNO,
	'A', -- Default rfid status
	@InoutboundType,
	ISNULL(@RecordTime, DATEADD(DAY, -7, GETDATE())),
	@Username,
	@Username,
   'Trace history at station ' + @TargetStationNO
)
;
