# Análisis de ventas e inventario para una farmacia pequeña

Este proyecto es un análisis de ventas, márgenes e inventario pensado para una farmacia independiente de barrio. Lo armé a partir de mi experiencia apoyando en la operación de una farmacia, donde vi que muchas decisiones (qué resurtir, qué se está caducando, de dónde sale la utilidad) se toman "a ojo".

> **Los datos son simulados.** No son de ningún negocio real. Los generé con `data/generar_datos.py` para que tuvieran un comportamiento realista (pocos productos venden casi todo, temporada de gripa, márgenes distintos por categoría) sin exponer información privada.

## Preguntas que responde

1. ¿Cómo se comportan las ventas y la utilidad bruta mes a mes?
2. ¿Qué categorías dejan más margen y cuáles solo mueven volumen?
3. ¿Qué productos concentran la venta? (análisis ABC / Pareto)
4. ¿Qué lotes se van a caducar antes de venderse y cuánto dinero hay en riesgo?
5. ¿Qué productos hay que resurtir hoy? (punto de reorden)

## Hallazgos (con los datos simulados)

- **30 de 120 productos (25%) generan el 80% de la venta.** Esos son los que nunca pueden faltar en anaquel.
- **Los genéricos dejan ~45% de margen y los de patente ~18%.** Patente vende mucho, pero genérico deja más utilidad por cada peso vendido.
- **28 lotes con caducidad en menos de 90 días no alcanzan a venderse al ritmo actual**, con ~$101,000 MXN de costo en riesgo. Solo 4 lotes de patente concentran ~$61,000: ahí conviene negociar devolución con el proveedor o moverlos con promoción.
- **La temporada de nov–feb vende ~25% más** que el resto del año, así que el inventario debe crecer antes de esos meses, no durante.

![Ventas mensuales](img/ventas_mensuales.png)
![Margen por categoría](img/margen_categoria.png)
![Curva de Pareto](img/pareto_abc.png)

## Cómo está hecho

| Parte | Herramienta | Archivo |
| --- | --- | --- |
| Generación de datos | Python (numpy, pandas) | `data/generar_datos.py` |
| Base de datos | SQLite | se crea al correr `analisis.py` |
| Consultas de negocio | SQL (JOINs, CTEs, funciones de ventana) | `sql/consultas.sql` |
| Punto de reorden y gráficas | Python (pandas, matplotlib) | `analisis.py` |

## Cómo correrlo

```bash
pip install pandas numpy matplotlib
python data/generar_datos.py   # opcional: los CSV ya vienen incluidos
python analisis.py
```

## Siguientes pasos

- Pasar las gráficas a un dashboard en Power BI.
- Conectar el análisis a una exportación real del punto de venta (con datos anonimizados).

---

**English summary:** Sales, margin and inventory analysis for a small independent pharmacy, using simulated data. SQL (SQLite, CTEs, window functions) answers the business questions; Python (pandas, matplotlib) computes reorder points and charts. Key findings: 25% of products drive 80% of sales, generics carry ~45% margin vs ~18% for brand-name drugs, and ~MXN 101k of inventory cost is at risk of expiring within 90 days.
