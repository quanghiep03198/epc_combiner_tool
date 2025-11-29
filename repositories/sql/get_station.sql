DECLARE @mo_no NVARCHAR(10) = 'VA1';

SELECT DISTINCT device_name AS station_no,
CASE 
   WHEN device_name LIKE '%P%' THEN 4
   WHEN device_name LIKE '%IH%' THEN 3
   WHEN device_name LIKE '%DH%' THEN 2
   WHEN device_name LIKE '%M%' THEN 1
   ELSE 1
END AS station_seq_no
FROM DV_DATA_LAKE.dbo.dv_rfidreader 
WHERE device_name NOT LIKE 'CUS%' -- Exclude customer RFID readers
AND device_name NOT LIKE '%_FC%' -- Exclude FC department RFID readers
AND device_name LIKE CONCAT('%', @mo_no, '%') 
ORDER BY
station_seq_no ASC,
device_name ASC;