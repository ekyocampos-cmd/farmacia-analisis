-- Consultas de negocio sobre la base farmacia.db (SQLite).
-- La base se crea con `python analisis.py`, que carga los CSV de /data.

-- 1. Ventas, utilidad bruta y margen por mes
SELECT strftime('%Y-%m', fecha)                         AS mes,
       ROUND(SUM(venta), 0)                             AS ventas,
       ROUND(SUM(venta - costo_total), 0)               AS utilidad_bruta,
       ROUND(100.0 * SUM(venta - costo_total) / SUM(venta), 1) AS margen_pct
FROM ventas
GROUP BY mes
ORDER BY mes;

-- 2. Margen por categoría: ¿de dónde sale realmente la utilidad?
SELECT p.categoria,
       ROUND(SUM(v.venta), 0)                                   AS ventas,
       ROUND(SUM(v.venta - v.costo_total), 0)                   AS utilidad_bruta,
       ROUND(100.0 * SUM(v.venta - v.costo_total) / SUM(v.venta), 1) AS margen_pct
FROM ventas v
JOIN productos p USING (producto_id)
GROUP BY p.categoria
ORDER BY utilidad_bruta DESC;

-- 3. Top 10 productos por utilidad bruta
SELECT p.nombre, p.categoria,
       SUM(v.unidades)                         AS unidades,
       ROUND(SUM(v.venta - v.costo_total), 0)  AS utilidad_bruta
FROM ventas v
JOIN productos p USING (producto_id)
GROUP BY p.producto_id
ORDER BY utilidad_bruta DESC
LIMIT 10;

-- 4. Clasificación ABC (A = productos que suman el 80% de la venta)
WITH por_producto AS (
    SELECT producto_id, SUM(venta) AS venta
    FROM ventas
    GROUP BY producto_id
),
acumulado AS (
    SELECT producto_id, venta,
           SUM(venta) OVER (ORDER BY venta DESC) * 1.0 / SUM(venta) OVER () AS pct_acum
    FROM por_producto
)
SELECT CASE WHEN pct_acum <= 0.80 THEN 'A'
            WHEN pct_acum <= 0.95 THEN 'B'
            ELSE 'C' END              AS clase,
       COUNT(*)                       AS productos,
       ROUND(SUM(venta), 0)           AS ventas
FROM acumulado
GROUP BY clase
ORDER BY clase;

-- 5. Lotes en riesgo: caducan en menos de 90 días y no se venderán a tiempo
WITH rotacion AS (
    SELECT producto_id, SUM(unidades) / 365.0 AS unidades_dia
    FROM ventas
    GROUP BY producto_id
)
SELECT p.nombre, l.existencia, l.caducidad,
       CAST(julianday(l.caducidad) - julianday('2026-10-31') AS INT) AS dias_para_caducar,
       ROUND(COALESCE(r.unidades_dia, 0) *
             (julianday(l.caducidad) - julianday('2026-10-31')), 1)  AS unidades_que_se_venderian,
       ROUND(l.existencia * p.costo, 0)                              AS costo_en_riesgo
FROM lotes l
JOIN productos p USING (producto_id)
LEFT JOIN rotacion r USING (producto_id)
WHERE julianday(l.caducidad) - julianday('2026-10-31') <= 90
  AND COALESCE(r.unidades_dia, 0) * (julianday(l.caducidad) - julianday('2026-10-31')) < l.existencia
ORDER BY costo_en_riesgo DESC;
