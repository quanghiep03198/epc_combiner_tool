COMPENSATE_ASSEMBLY_SQL = f"""--sql
DECLARE @Username NVARCHAR(50) = :username;
DECLARE @FactoryCode NVARCHAR(50) = :factory_code;
DECLARE @PendingCombineEpcs NVARCHAR(MAX) = :pending_combine_epcs;

-- * Define the temporary table to store the Pending combine EPCs
DECLARE @EpcTable TABLE (
    EPC_Code NVARCHAR (50));

INSERT INTO @EpcTable
SELECT value
FROM   STRING_SPLIT (@PendingCombineEpcs, ',');

-- * Define the station order mapping base on the process at the factory
DECLARE @StationOrderMapping TABLE (
    station_like  NVARCHAR (50),
    station_order INT          );

INSERT  INTO @StationOrderMapping (
    station_like,
    station_order
)
VALUES                            ('%FC%', 1),
                                  ('%M%', 2),
                                  ('%DH%', 3),
                                  ('%IH%', 4),
                                  ('%P%101', 5),
                                  ('%P%103', 6);

DECLARE @LastStationOrder AS INT = (SELECT MAX(station_order)
                                    FROM   @StationOrderMapping);

-- * Define the expected station gap and preparation to recall duration
DECLARE @EXPECTED_STATION_GAP AS INT = 30;

DECLARE @PREPARATION_TO_RECALL_DURATION AS INT = 5;

DECLARE @CompensatingRemark AS NVARCHAR (MAX) = 'Compensating for assembly line ":station"';

-- * Table get latest record time at assembly line by Manufacturing order
DECLARE @LatestAssemblyByMo TABLE (
    mo_no NVARCHAR (50),
    stationNO NVARCHAR (50),
    record_time DATETIME
);

INSERT INTO @LatestAssemblyByMo
SELECT  mo_no,
       stationNO,
       MAX(record_time) AS record_time
FROM   
       DV_DATA_LAKE.dbo.dv_RFIDrecordmst_backup_Daily AS a
WHERE  EPC_Code IN (SELECT value FROM STRING_SPLIT(@PendingCombineEpcs, ','))
       AND stationNO LIKE '%P%103'
GROUP BY mo_no,
         stationNO
ORDER BY MAX(record_time) DESC;

WITH   EPC_STATION_HISTORY
AS     (SELECT a.keyid,
               a.EPC_Code,
               a.mo_no,
               a.size_numcode,
               (SELECT TOP 1 mo_no FROM dv_rfidmatchmst WHERE ri_cancel = 1 ORDER BY ri_cancel_date DESC) AS recent_mo_no,
               ISNULL(rbk.stationNO, r.stationNO) AS stationNO,
               ISNULL(rbk.record_time, r.record_time) AS record_time,
               DATEDIFF(DAY, ISNULL(rbk.record_time, r.record_time), GETDATE()) AS days_since_last_record,
               CASE WHEN ISNULL(rbk.stationNO, r.stationNO) LIKE '%FC%' THEN 1
                    WHEN ISNULL(rbk.stationNO, r.stationNO) LIKE '%M%' THEN 2
                    WHEN ISNULL(rbk.stationNO, r.stationNO) LIKE '%DH%' THEN 3
                    WHEN ISNULL(rbk.stationNO, r.stationNO) LIKE '%IH%' THEN 4
                    WHEN ISNULL(rbk.stationNO, r.stationNO) LIKE '%P%101' THEN 5
                    WHEN ISNULL(rbk.stationNO, r.stationNO) LIKE '%P%103' THEN 6
                    ELSE NULL END AS latest_station_order,
               ROW_NUMBER() OVER (PARTITION BY a.keyid, a.EPC_Code ORDER BY ISNULL(rbk.record_time, r.record_time) DESC) AS rn
        FROM   DV_DATA_LAKE.dbo.dv_rfidmatchmst AS a
               INNER JOIN
               @EpcTable AS e
               ON a.EPC_Code = e.EPC_Code
               LEFT OUTER JOIN
               (SELECT matchkeyid,
                       EPC_Code,
                       mo_no,
                       size_code,
                       stationNO,
                       record_time
                FROM   DV_DATA_LAKE.dbo.dv_RFIDrecordmst
                WHERE  EPC_Code IN (SELECT EPC_Code
                                    FROM   @EpcTable)) AS r
               ON a.keyid = r.matchkeyid
                  AND a.EPC_Code = r.EPC_Code
               LEFT OUTER JOIN
               (SELECT matchkeyid,
                       EPC_Code,
                       mo_no,
                       size_code,
                       stationNO,
                       record_time
                FROM   DV_DATA_LAKE.dbo.dv_RFIDrecordmst_backup_Daily
                WHERE  EPC_Code IN (SELECT EPC_Code
                                    FROM   @EpcTable)) AS rbk
               ON a.keyid = rbk.matchkeyid
                  AND a.EPC_Code = rbk.EPC_Code
                
        WHERE  a.ri_cancel = 0),
-- * Get the latest assembly line record for each `mo_no` in previous life cycle
-- * (one row per mo_no: the 103 station with the newest record_time)
LATEST_ASSEMBLY_BY_MO
AS (SELECT * FROM @LatestAssemblyByMo),
REDUCED_DATASOURCE
AS     (SELECT a.keyid,
               a.EPC_Code,
               a.mo_no,
               a.size_numcode,
               a.latest_station_order,
               a.stationNO AS lastest_station,
               ISNULL(b.record_time, a.record_time) AS latest_record_time,
               CASE
                    -- * If the latest station is Assembly 101 -> expect the last station (103)
                    WHEN a.latest_station_order = @LastStationOrder - 1 THEN REPLACE(a.stationNO, '101', '103')
                    -- * If the latest station is not Assembly (neither 101 nor 103) -> Using latest Assembly line station by previous `mo_no`
                    WHEN a.latest_station_order < @LastStationOrder - 1 THEN IIF(b.stationNO IS NOT NULL, b.stationNO, CONCAT_WS('_', @FactoryCode, 'PA103'))
                    -- * If the latest station is the last station, then we expect the same station (103)
                    ELSE IIF(b.stationNO IS NOT NULL, b.stationNO, CONCAT_WS('_', @FactoryCode, 'PA103'))
               END AS expecting_assembly_station,
               CASE WHEN a.days_since_last_record = 0 THEN DATEADD(MINUTE, -5, GETDATE())
                    WHEN a.days_since_last_record = 1 THEN DATEADD(MINUTE, @EXPECTED_STATION_GAP * (@LastStationOrder - a.latest_station_order), a.record_time)
                    ELSE DATEADD(DAY, -1, GETDATE()) END AS expecting_record_time,
               ROW_NUMBER() OVER (PARTITION BY a.keyid, a.EPC_Code ORDER BY a.latest_station_order DESC) AS rn
        FROM   EPC_STATION_HISTORY AS a
               LEFT JOIN
               LATEST_ASSEMBLY_BY_MO AS b
               ON a.mo_no = b.mo_no)
MERGE INTO DV_DATA_LAKE.dbo.dv_RFIDrecordmst AS target
USING (
    SELECT keyid, EPC_Code, mo_no, size_numcode, expecting_assembly_station, expecting_record_time 
    FROM REDUCED_DATASOURCE
    WHERE rn = 1 AND lastest_station NOT LIKE '%P%103'
) AS source
ON target.matchkeyid = source.keyid 
    AND target.EPC_Code = source.EPC_Code
    AND target.mo_no = source.mo_no
    AND target.size_code = source.size_numcode
    AND target.stationNO = source.expecting_assembly_station
WHEN NOT MATCHED BY TARGET THEN 
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
"""
