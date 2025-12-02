DECLARE @FactoryCode NVARCHAR(10) = :factory_code;

SELECT DISTINCT device_name AS station_no,
CASE 
   WHEN device_name LIKE '%FC%' THEN 1
   WHEN device_name LIKE '%M%' THEN 2
   WHEN device_name LIKE '%DH%' THEN 3
   WHEN device_name LIKE '%IH%' THEN 4
   WHEN device_name LIKE '%P%101%' THEN 5
   WHEN device_name LIKE '%P%103%' THEN 6
   ELSE 999
END AS station_seq_no
FROM DV_DATA_LAKE.dbo.dv_rfidreader 
WHERE device_name NOT LIKE 'CUS%' -- Exclude customer RFID readers
AND device_name NOT LIKE '%FC%' -- Exclude FC department RFID readers
AND device_name LIKE CONCAT('%', @FactoryCode, '%') 
ORDER BY
station_seq_no ASC,
device_name ASC;