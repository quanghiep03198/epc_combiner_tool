SELECT
	a.or_no
  , a.size_code
  , b.size_numcode
  , b.size_qty
FROM ta_ordersizerun a
  CROSS APPLY (
    VALUES
		([size_numcode01], [size_qty01])
      ,
		([size_numcode02], [size_qty02])
      ,
		([size_numcode03], [size_qty03])
      ,
		([size_numcode04], [size_qty04])
      ,
		([size_numcode05], [size_qty05])
      ,
		([size_numcode06], [size_qty06])
      ,
		([size_numcode07], [size_qty07])
      ,
		([size_numcode08], [size_qty08])
      ,
		([size_numcode09], [size_qty09])
      ,
		([size_numcode10], [size_qty10])
      ,
		([size_numcode11], [size_qty11])
      ,
		([size_numcode12], [size_qty12])
      ,
		([size_numcode13], [size_qty13])
      ,
		([size_numcode14], [size_qty14])
      ,
		([size_numcode15], [size_qty15])
      ,
		([size_numcode16], [size_qty16])
      ,
		([size_numcode17], [size_qty17])
      ,
		([size_numcode18], [size_qty18])
      ,
		([size_numcode19], [size_qty19])
      ,
		([size_numcode20], [size_qty20])
      ,
		([size_numcode21], [size_qty21])
      ,
		([size_numcode22], [size_qty22])
      ,
		([size_numcode23], [size_qty23])
      ,
		([size_numcode24], [size_qty24])
      ,
		([size_numcode25], [size_qty25])
      ,
		([size_numcode26], [size_qty26])
      ,
		([size_numcode27], [size_qty27])
      ,
		([size_numcode28], [size_qty28])
      ,
		([size_numcode29], [size_qty29])
      ,
		([size_numcode30], [size_qty30])
      ,
		([size_numcode31], [size_qty31])
      ,
		([size_numcode32], [size_qty32])
      ,
		([size_numcode33], [size_qty33])
      ,
		([size_numcode34], [size_qty34])
      ,
		([size_numcode35], [size_qty35])
      ,
		([size_numcode36], [size_qty36])
      ,
		([size_numcode37], [size_qty37])
      ,
		([size_numcode38], [size_qty38])
      ,
		([size_numcode39], [size_qty39])
      ,
		([size_numcode40], [size_qty40])
  ) b (
    [size_numcode],[size_qty]
  )
WHERE [size_qty] <> 0
	and a.isactive= 'Y'
	and a.or_no= @or_no