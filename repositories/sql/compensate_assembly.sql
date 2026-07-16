DECLARE @Username NVARCHAR(50) = :username;
DECLARE @FactoryCode NVARCHAR(50) = :factory_code;
DECLARE @PendingCombineEpcs NVARCHAR(MAX) = :pending_combine_epcs;

-- * Define the temporary table to store the Pending combine EPCs
DECLARE @EpcTable TABLE (EPC_Code NVARCHAR(50));
INSERT INTO @EpcTable 
SELECT value FROM STRING_SPLIT(@PendingCombineEpcs, ',');

-- * Define the station order mapping base on the process at the factory
DECLARE @StationOrderMapping TABLE (station_like NVARCHAR(50), station_order INT);
INSERT INTO @StationOrderMapping (station_like, station_order)
VALUES 
    ('%FC%', 1),
    ('%M%', 2),
    ('%DH%', 3),
    ('%IH%', 4),
    ('%P%101%', 5),
    ('%P%103%', 6)
;
DECLARE @LastStationOrder INT = (SELECT MAX(station_order) FROM @StationOrderMapping);

-- * Define the expected station gap and preparation to recall duration
DECLARE @EXPECTED_STATION_GAP INT = 30;
DECLARE @PREPARATION_TO_RECALL_DURATION  INT = 5;

DECLARE @CompensatingRemark NVARCHAR(MAX) = 'Compensating for assembly line ":station" before starting combine new again';

WITH EPC_STATION_HISTORY AS (
    SELECT 
        a.keyid, 
        a.EPC_Code, 
        a.mo_no, 
        a.size_numcode, 
        ISNULL(r.stationNO, rbk.stationNO) AS stationNO, 
        ISNULL(r.record_time, rbk.record_time) AS record_time,
        DATEDIFF(DAY, ISNULL(r.record_time, rbk.record_time), GETDATE()) AS days_since_last_record,
        som.station_order AS latest_station_order, 
        ROW_NUMBER() OVER (PARTITION BY a.keyid, a.EPC_Code ORDER BY ISNULL(r.record_time, rbk.record_time) DESC) AS rn
    FROM DV_DATA_LAKE.dbo.dv_rfidmatchmst a
    INNER JOIN @EpcTable AS e ON a.EPC_Code = e.EPC_Code
    LEFT JOIN (
        SELECT matchkeyid, EPC_Code, mo_no, size_code, stationNO, record_time
        FROM DV_DATA_LAKE.dbo.dv_RFIDrecordmst
        WHERE EPC_Code IN (SELECT EPC_Code FROM @EpcTable)
    ) r ON a.keyid = r.matchkeyid AND a.EPC_Code = r.EPC_Code
    LEFT JOIN (
        SELECT matchkeyid, EPC_Code, mo_no, size_code, stationNO, record_time
        FROM DV_DATA_LAKE.dbo.dv_RFIDrecordmst_backup_Daily
        WHERE EPC_Code IN (SELECT EPC_Code FROM @EpcTable)
    ) rbk ON a.keyid = rbk.matchkeyid AND a.EPC_Code = rbk.EPC_Code
    LEFT JOIN @StationOrderMapping AS som ON ISNULL(r.stationNO, rbk.stationNO) LIKE som.station_like
    WHERE a.ri_cancel = 0
),
REDUCED_DATASOURCE AS (
    SELECT 
        keyid, 
        EPC_Code,
        mo_no, 
        size_numcode , 
        latest_station_order,
        stationNO AS lastest_station,
        record_time AS latest_record_time, -- LATEST RECORD TIME AT LAST STATION
        CASE 
            WHEN latest_station_order < @LastStationOrder - 1 THEN CONCAT_WS('_', @FactoryCode, 'PA103')   -- * Nếu chưa đi đến thành hình thì bù mặc định cho thành hình A (103)
            WHEN latest_station_order = @LastStationOrder - 1 THEN REPLACE(stationNO, '101', '103')        -- * Nếu chỉ đi đến đầu thành hình (101) thì bù cho thành hình tương ứng (103)
            ELSE stationNO                                                      -- * Nếu đã đi đến thành hình (103) thì giữ nguyên
        END AS expecting_assembly_station, 
        CASE 
            WHEN days_since_last_record = 0 THEN DATEADD(MINUTE, -5, GETDATE())
            WHEN days_since_last_record = 1 THEN DATEADD(MINUTE, @EXPECTED_STATION_GAP * (@LastStationOrder - latest_station_order), record_time)
            ELSE DATEADD(DAY, -1, record_time)
        END AS expecting_record_time, 
        ROW_NUMBER() OVER (PARTITION BY keyid, EPC_Code ORDER BY latest_station_order DESC) AS rn
    FROM EPC_STATION_HISTORY a
)
MERGE INTO DV_DATA_LAKE.dbo.dv_RFIDrecordmst AS target
USING (
    SELECT keyid, EPC_Code, mo_no, size_numcode, expecting_assembly_station, expecting_record_time 
    FROM REDUCED_DATASOURCE 
    WHERE rn = 1
) AS source
ON target.matchkeyid = source.keyid 
    AND target.EPC_Code = source.EPC_Code
    AND target.mo_no = source.mo_no
    AND target.size_code = source.size_numcode
    AND target.stationNO = source.expecting_assembly_station
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
        source.size_numcode, 
        @FactoryCode,
        source.expecting_assembly_station,
        'A', -- Default rfid status
        'A',
        source.expecting_record_time, 
        @Username,
        @Username,
        REPLACE(@CompensatingRemark, ':station', source.expecting_assembly_station)
    )
;