DECLARE @MoNo NVARCHAR(10) = :mo_no;
DECLARE @SizeNumCode NVARCHAR(10) = :size_numcode;
DECLARE @MaxStationSeqNo INT = :station_seq_no;

WITH BaseData AS (
   SELECT 
      stationNO,
      record_time,
      -- * Pre-calculate station type to avoid repeated CASE
      CASE 
         WHEN stationNO LIKE '%FC%' THEN 1
         WHEN stationNO LIKE '%M%' THEN 2
         WHEN stationNO LIKE '%DH%' THEN 3
         WHEN stationNO LIKE '%IH%' THEN 4
         WHEN stationNO LIKE '%P%101' THEN 5
         WHEN stationNO LIKE '%P%103' THEN 6
         ELSE 999
      END AS station_seq_no,
      -- * Determine station type for branching
      CASE 
         WHEN stationNO LIKE '%M%' THEN 'PARALLEL'
         WHEN stationNO LIKE '%PA101' OR stationNO LIKE '%PB101' 
            OR stationNO LIKE '%PA103' OR stationNO LIKE '%PB103' THEN 'PARALLEL'
         ELSE 'OTHER'
      END AS station_type
   FROM DV_DATA_LAKE.dbo.dv_RFIDrecordmst WITH (NOLOCK)
   WHERE 
      mo_no = @MoNo
      AND size_code = @SizeNumCode
      AND stationNO NOT LIKE '%P%102'
      AND stationNO NOT LIKE 'CUS%'
   UNION ALL
   SELECT 
      stationNO,
      record_time,
      -- * Pre-calculate station type to avoid repeated CASE
      CASE 
         WHEN stationNO LIKE '%FC%' THEN 1
         WHEN stationNO LIKE '%M%' THEN 2
         WHEN stationNO LIKE '%DH%' THEN 3
         WHEN stationNO LIKE '%IH%' THEN 4
         WHEN stationNO LIKE '%P%101' THEN 5
         WHEN stationNO LIKE '%P%103' THEN 6
         ELSE 999
      END AS station_seq_no,
      -- * Determine station type for branching
      CASE 
         WHEN stationNO LIKE '%M%' THEN 'PARALLEL'
         WHEN stationNO LIKE '%P%101' 
            OR stationNO LIKE '%P%103' THEN 'PARALLEL'
         ELSE 'OTHER'
      END AS station_type
   FROM DV_DATA_LAKE.dbo.dv_RFIDrecordmst_backup_Daily WITH (NOLOCK)
   WHERE 
      mo_no = @MoNo
      AND size_code = @SizeNumCode
      AND stationNO NOT LIKE '%P%102'
      AND stationNO NOT LIKE 'CUS%'

),
ParallelStations AS (
   -- * Handle parallel stations (M, PA/PB/.../PG 101-103)
   SELECT 
      stationNO,
      record_time,
      station_seq_no,
      -- * Group key to deduplicate
      CASE 
         WHEN stationNO LIKE '%M%' THEN 'M'
         ELSE RIGHT(stationNO, 3)
      END AS group_key,
      CASE 
         WHEN stationNO LIKE '%PA%' THEN 1
         WHEN stationNO LIKE '%PB%' THEN 2
         WHEN stationNO LIKE '%PC%' THEN 3
         WHEN stationNO LIKE '%PD%' THEN 4
         WHEN stationNO LIKE '%PE%' THEN 5
         WHEN stationNO LIKE '%PF%' THEN 6
         WHEN stationNO LIKE '%PG%' THEN 7
         ELSE 8
      END AS priority,
      ROW_NUMBER() OVER (
         PARTITION BY 
            CASE 
               WHEN stationNO LIKE '%M%' THEN 'M'
               ELSE RIGHT(stationNO, 3)
            END
         ORDER BY 
            CASE 
               WHEN stationNO LIKE '%PA%' THEN 1
               WHEN stationNO LIKE '%PB%' THEN 2
               WHEN stationNO LIKE '%PC%' THEN 3
               WHEN stationNO LIKE '%PD%' THEN 4
               WHEN stationNO LIKE '%PE%' THEN 5
               WHEN stationNO LIKE '%PF%' THEN 6
               WHEN stationNO LIKE '%PG%' THEN 7
               ELSE 8
            END,
            record_time ASC
      ) AS rn
   FROM BaseData
   WHERE station_type = 'PARALLEL'
),
OtherStations AS (
   -- * Other stations (not M or P)
   SELECT DISTINCT
      stationNO,
      MAX(record_time) AS record_time,
      MAX(station_seq_no) AS station_seq_no
   FROM BaseData
   WHERE station_type = 'OTHER'
   GROUP BY stationNO
)
-- * Final selection combining both parallel and other stations
SELECT 
   stationNO AS station_no, 
   DATEADD(DAY, -7, record_time) AS last_record_time,
   station_seq_no
FROM ParallelStations
WHERE rn = 1
AND station_seq_no <= @MaxStationSeqNo
UNION ALL
SELECT 
   stationNO AS station_no, 
   DATEADD(DAY, -7, record_time) AS last_record_time,
   station_seq_no
FROM OtherStations
WHERE station_seq_no <= @MaxStationSeqNo
ORDER BY station_seq_no ASC, last_record_time ASC, stationNO ASC;