GET_SIZE_QTY_SQL = f"""--sql
DECLARE @mo_no NVARCHAR(10) = :mo_no;
DECLARE @mo_noseq NVARCHAR(10) = :mo_noseq;

SELECT
    a.size_code,
        b.size_numcode,
            SUM(CAST(b.size_qty AS INT)) AS size_qty,
            ISNULL(CAST(c.combined_qty AS INT), 0) AS combined_qty,
            ISNULL(CAST(d.in_use_qty AS INT), 0) AS in_use_qty,
            ISNULL(CAST(e.compensated_qty AS INT), 0) AS compensated_qty,
            ISNULL(CAST(f.cancelled_qty AS INT), 0) AS cancelled_qty,
            IIF(
                ISNULL(CAST(g.max_add_qty AS INT), 0) >= SUM(CAST(b.size_qty AS INT)) - ISNULL(CAST(d.in_use_qty AS INT), 0),
                SUM(CAST(b.size_qty AS INT)) - ISNULL(CAST(d.in_use_qty AS INT), 0),
                ISNULL(CAST(g.max_add_qty AS INT), 0) - ISNULL(CAST(d.in_use_qty AS INT), 0)
            ) AS max_add_qty
FROM wuerp_vnrd.dbo.ta_ordersizerun a WITH (NOLOCK)
    LEFT JOIN wuerp_vnrd.dbo.ta_ordermst or1 WITH (NOLOCK) ON or1.or_no = a.or_no
        AND or1.isactive = 'Y'
    LEFT JOIN wuerp_vnrd.dbo.ta_manufacturdet a1 WITH (NOLOCK) ON or1.or_no = a1.or_no
        AND a1.isactive = 'Y' AND (@mo_noseq IS NULL OR a1.mo_noseq = @mo_noseq)
OUTER APPLY (
  VALUES
    ([size_numcode01], ISNULL(size_qty01, 0) - ISNULL(size_qtycancel01, 0)),
    ([size_numcode02], ISNULL(size_qty02, 0) - ISNULL(size_qtycancel02, 0)),
    ([size_numcode03], ISNULL(size_qty03, 0) - ISNULL(size_qtycancel03, 0)),
    ([size_numcode04], ISNULL(size_qty04, 0) - ISNULL(size_qtycancel04, 0)),
    ([size_numcode05], ISNULL(size_qty05, 0) - ISNULL(size_qtycancel05, 0)),
    ([size_numcode06], ISNULL(size_qty06, 0) - ISNULL(size_qtycancel06, 0)),
    ([size_numcode07], ISNULL(size_qty07, 0) - ISNULL(size_qtycancel07, 0)),
    ([size_numcode08], ISNULL(size_qty08, 0) - ISNULL(size_qtycancel08, 0)),
    ([size_numcode09], ISNULL(size_qty09, 0) - ISNULL(size_qtycancel09, 0)),
    ([size_numcode10], ISNULL(size_qty10, 0) - ISNULL(size_qtycancel10, 0)),
    ([size_numcode11], ISNULL(size_qty11, 0) - ISNULL(size_qtycancel11, 0)),
    ([size_numcode12], ISNULL(size_qty12, 0) - ISNULL(size_qtycancel12, 0)),
    ([size_numcode13], ISNULL(size_qty13, 0) - ISNULL(size_qtycancel13, 0)),
    ([size_numcode14], ISNULL(size_qty14, 0) - ISNULL(size_qtycancel14, 0)),
    ([size_numcode15], ISNULL(size_qty15, 0) - ISNULL(size_qtycancel15, 0)),
    ([size_numcode16], ISNULL(size_qty16, 0) - ISNULL(size_qtycancel16, 0)),
    ([size_numcode17], ISNULL(size_qty17, 0) - ISNULL(size_qtycancel17, 0)),
    ([size_numcode18], ISNULL(size_qty18, 0) - ISNULL(size_qtycancel18, 0)),
    ([size_numcode19], ISNULL(size_qty19, 0) - ISNULL(size_qtycancel19, 0)),
    ([size_numcode20], ISNULL(size_qty20, 0) - ISNULL(size_qtycancel20, 0)),
    ([size_numcode21], ISNULL(size_qty21, 0) - ISNULL(size_qtycancel21, 0)),
    ([size_numcode22], ISNULL(size_qty22, 0) - ISNULL(size_qtycancel22, 0)),
    ([size_numcode23], ISNULL(size_qty23, 0) - ISNULL(size_qtycancel23, 0)),
    ([size_numcode24], ISNULL(size_qty24, 0) - ISNULL(size_qtycancel24, 0)),
    ([size_numcode25], ISNULL(size_qty25, 0) - ISNULL(size_qtycancel25, 0)),
    ([size_numcode26], ISNULL(size_qty26, 0) - ISNULL(size_qtycancel26, 0)),
    ([size_numcode27], ISNULL(size_qty27, 0) - ISNULL(size_qtycancel27, 0)),
    ([size_numcode28], ISNULL(size_qty28, 0) - ISNULL(size_qtycancel28, 0)),
    ([size_numcode29], ISNULL(size_qty29, 0) - ISNULL(size_qtycancel29, 0)),
    ([size_numcode30], ISNULL(size_qty30, 0) - ISNULL(size_qtycancel30, 0)),
    ([size_numcode31], ISNULL(size_qty31, 0) - ISNULL(size_qtycancel31, 0)),
    ([size_numcode32], ISNULL(size_qty32, 0) - ISNULL(size_qtycancel32, 0)),
    ([size_numcode33], ISNULL(size_qty33, 0) - ISNULL(size_qtycancel33, 0)),
    ([size_numcode34], ISNULL(size_qty34, 0) - ISNULL(size_qtycancel34, 0)),
    ([size_numcode35], ISNULL(size_qty35, 0) - ISNULL(size_qtycancel35, 0)),
    ([size_numcode36], ISNULL(size_qty36, 0) - ISNULL(size_qtycancel36, 0)),
    ([size_numcode37], ISNULL(size_qty37, 0) - ISNULL(size_qtycancel37, 0)),
    ([size_numcode38], ISNULL(size_qty38, 0) - ISNULL(size_qtycancel38, 0)),
    ([size_numcode39], ISNULL(size_qty39, 0) - ISNULL(size_qtycancel39, 0)),
    ([size_numcode40], ISNULL(size_qty40, 0) - ISNULL(size_qtycancel40, 0))
) b (
  [size_numcode],[size_qty]
)
-- tổng số lượng đã phối
OUTER APPLY (
    SELECT COUNT(EPC_Code)
    FROM DV_DATA_LAKE.dbo.dv_rfidmatchmst
    WHERE mo_no = a1.mo_no
        AND (@mo_noseq IS NULL OR mo_noseq = @mo_noseq)
        AND size_numcode = b.size_numcode
        AND sole_tag = 'A'
        AND isactive = 'Y'
        AND ri_type = 'A'
    GROUP BY size_code, size_numcode
) c ([combined_qty])
OUTER APPLY (
    SELECT COUNT(EPC_Code) AS in_use_qty
    FROM DV_DATA_LAKE.dbo.dv_rfidmatchmst
    WHERE mo_no = a1.mo_no
        AND (@mo_noseq IS NULL OR mo_noseq = @mo_noseq)
        AND size_numcode = b.size_numcode
        AND ri_cancel = 0
        AND sole_tag = 'A'
        AND isactive = 'Y'
    GROUP BY size_code, size_numcode
) d ([in_use_qty])
OUTER APPLY (
    SELECT COUNT(EPC_Code) AS compensated_qty
    FROM DV_DATA_LAKE.dbo.dv_rfidmatchmst
    WHERE mo_no = a1.mo_no
        AND size_numcode = b.size_numcode
        AND ri_type = 'D'
        AND sole_tag = 'A'
        AND isactive = 'Y'
        AND (@mo_noseq IS NULL OR mo_noseq = @mo_noseq)
    GROUP BY size_code, size_numcode
) e ([compensated_qty])
OUTER APPLY (
    SELECT COUNT(EPC_Code) AS cancelled_qty
    FROM DV_DATA_LAKE.dbo.dv_rfidmatchmst
    WHERE mo_no = a1.mo_no
        AND size_numcode = b.size_numcode AND ri_cancel = 1 AND sole_tag = 'A'
        AND (@mo_noseq IS NULL OR mo_noseq = @mo_noseq)
    GROUP BY size_code, size_numcode
) f ([cancelled_qty])
OUTER APPLY (
    SELECT COUNT(DISTINCT EPC_Code) AS max_add_qty
    FROM DV_DATA_LAKE.dbo.dv_rfidmatchmst
    WHERE mo_no = a1.mo_no
        AND size_numcode = b.size_numcode AND ri_cancel = 0 AND sole_tag = 'A'
        AND mo_noseq = '001'
    GROUP BY size_code, size_numcode
) g ([max_add_qty])
WHERE b.size_qty <> 0
    AND a.isactive= 'Y'
    AND a1.mo_no = @mo_no
    AND (@mo_noseq IS NULL OR a1.mo_noseq = @mo_noseq)
GROUP BY a.size_code, b.size_numcode, c.combined_qty, d.in_use_qty, e.compensated_qty, f.cancelled_qty, g.max_add_qty
ORDER BY RIGHT('0000' + IIF(CHARINDEX('.', b.size_numcode) > 0, b.size_numcode, b.size_numcode + '.0'), 5) ASC
OPTION (OPTIMIZE FOR UNKNOWN);
"""
