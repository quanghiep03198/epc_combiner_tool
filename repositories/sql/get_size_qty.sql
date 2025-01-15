SELECT
    a.size_code,
    CASE WHEN LEN(b.size_numcode) = 1 THEN CONCAT(0,b.size_numcode) ELSE b.size_numcode END [size_numcode], 
    SUM(CAST(b.size_qty AS INT)) AS size_qty,
    ISNULL(SUM(CAST(c.combined_qty AS INT)), 0) AS combined_qty,
    ISNULL(SUM(CAST(d.in_use_qty AS INT)), 0) AS in_use_qty,
    ISNULL(SUM(CAST(e.compensated_qty AS INT)), 0) AS compensated_qty,
    ISNULL(SUM(CAST(f.cancelled_qty AS INT)), 0) AS cancelled_qty
FROM wuerp_vnrd.dbo.ta_ordersizerun a
    LEFT JOIN wuerp_vnrd.dbo.ta_ordermst or1 ON or1.or_no= a.or_no
        AND or1.isactive= 'Y'
    LEFT JOIN wuerp_vnrd.dbo.ta_manufacturdet a1 ON or1.or_no= a1.or_no
        AND a1.isactive= 'Y'
OUTER APPLY (
  VALUES
        ([size_numcode01], [size_qty01]),
        ([size_numcode02], [size_qty02]),
        ([size_numcode03], [size_qty03]),
        ([size_numcode04], [size_qty04]),
        ([size_numcode05], [size_qty05]),
        ([size_numcode06], [size_qty06]),
        ([size_numcode07], [size_qty07]),
        ([size_numcode08], [size_qty08]),
        ([size_numcode09], [size_qty09]),
        ([size_numcode10], [size_qty10]),
        ([size_numcode11], [size_qty11]),
        ([size_numcode12], [size_qty12]),
        ([size_numcode13], [size_qty13]),
        ([size_numcode14], [size_qty14]),
        ([size_numcode15], [size_qty15]),
        ([size_numcode16], [size_qty16]),
        ([size_numcode17], [size_qty17]),
        ([size_numcode18], [size_qty18]),
        ([size_numcode19], [size_qty19]),
        ([size_numcode20], [size_qty20]),
        ([size_numcode21], [size_qty21]),
        ([size_numcode22], [size_qty22]),
        ([size_numcode23], [size_qty23]),
        ([size_numcode24], [size_qty24]),
        ([size_numcode25], [size_qty25]),
        ([size_numcode26], [size_qty26]),
        ([size_numcode27], [size_qty27]),
        ([size_numcode28], [size_qty28]),
        ([size_numcode29], [size_qty29]),
        ([size_numcode30], [size_qty30]),
        ([size_numcode31], [size_qty31]),
        ([size_numcode32], [size_qty32]),
        ([size_numcode33], [size_qty33]),
        ([size_numcode34], [size_qty34]),
        ([size_numcode35], [size_qty35]),
        ([size_numcode36], [size_qty36]),
        ([size_numcode37], [size_qty37]),
        ([size_numcode38], [size_qty38]),
        ([size_numcode39], [size_qty39]),
        ([size_numcode40], [size_qty40])
) b (
  [size_numcode],[size_qty]
)
OUTER APPLY (
    SELECT COUNT(EPC_Code) AS combined_qty
    FROM DV_DATA_LAKE.dbo.dv_rfidmatchmst
    WHERE mo_no = a1.mo_no AND size_numcode = b.size_numcode 
    GROUP BY size_code, size_numcode
) c ([combined_qty])
OUTER APPLY (
    SELECT COUNT(EPC_Code) AS in_use_qty
    FROM DV_DATA_LAKE.dbo.dv_rfidmatchmst
    WHERE mo_no = a1.mo_no AND size_numcode = b.size_numcode AND ri_cancel = 0
    GROUP BY size_code, size_numcode
) d ([in_use_qty])
OUTER APPLY (
    SELECT COUNT(EPC_Code) AS compensated_qty
    FROM DV_DATA_LAKE.dbo.dv_rfidmatchmst
    WHERE mo_no = a1.mo_no AND size_numcode = b.size_numcode AND ri_type = 'D'
    GROUP BY size_code, size_numcode
) e ([compensated_qty])
OUTER APPLY (
    SELECT COUNT(EPC_Code) AS cancelled_qty
    FROM DV_DATA_LAKE.dbo.dv_rfidmatchmst
    WHERE mo_no = a1.mo_no AND size_numcode = b.size_numcode AND ri_cancel = 1
    GROUP BY size_code, size_numcode
) f ([cancelled_qty])
WHERE b.size_qty <> 0
    AND a.isactive= 'Y'
    AND a1.mo_no = :mo_no
GROUP BY a.size_code,b.size_numcode
ORDER BY 
    CASE 
        WHEN ISNUMERIC(b.size_numcode) = 1 THEN CAST(b.size_numcode AS FLOAT)  -- Nếu là số, chuyển thành dạng số
        WHEN LEFT(b.size_numcode, 1) = 'K' THEN CAST(SUBSTRING(b.size_numcode, 2, LEN(b.size_numcode)) AS FLOAT) + 0.5 -- K6, K8 -> xử lý thêm 0.5
        ELSE 9999  -- Nếu không phải số, đẩy xuống cuối
END ASC;
