"""
Análisis de ventas e inventario de una farmacia pequeña (datos simulados).

1. Carga los CSV en una base SQLite (farmacia.db).
2. Corre las consultas de consultas.sql.
3. Calcula puntos de reorden con pandas.
4. Guarda las gráficas como PNG en la misma carpeta.

Uso:
    python generar_datos.py   # opcional, ya vienen los CSV
    python analisis.py
"""
import sqlite3
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

matplotlib.use("Agg")

RAIZ = Path(__file__).parent
DATA = IMG = RAIZ
IMG.mkdir(exist_ok=True)
pd.set_option("display.width", 120)

# --- 1. Cargar a SQLite --------------------------------------------------------
con = sqlite3.connect(RAIZ / "farmacia.db")
for tabla in ("productos", "ventas", "lotes"):
    pd.read_csv(DATA / f"{tabla}.csv").to_sql(tabla, con, if_exists="replace", index=False)

# --- 2. Consultas SQL ----------------------------------------------------------
consultas = [q.strip() for q in (RAIZ / "consultas.sql").read_text(encoding="utf-8").split(";") if "SELECT" in q]
titulos = ["Ventas por mes", "Margen por categoría", "Top 10 productos por utilidad",
           "Clasificación ABC", "Lotes en riesgo de caducar"]
res = {}
for titulo, q in zip(titulos, consultas):
    res[titulo] = pd.read_sql_query(q, con)
    print(f"\n=== {titulo} ===\n{res[titulo].to_string(index=False)}")

# --- 3. Punto de reorden ---------------------------------------------------------
# punto de reorden = demanda diaria promedio x días de entrega + stock de seguridad
DIAS_ENTREGA = 3
ventas = pd.read_csv(DATA / "ventas.csv", parse_dates=["fecha"])
diario = (ventas.groupby(["producto_id", "fecha"])["unidades"].sum()
          .unstack(fill_value=0).reindex(columns=pd.date_range("2025-11-01", "2026-10-31"), fill_value=0))
reorden = pd.DataFrame({
    "demanda_dia": diario.mean(axis=1),
    "desv_dia": diario.std(axis=1),
})
reorden["punto_reorden"] = (reorden["demanda_dia"] * DIAS_ENTREGA
                            + 1.65 * reorden["desv_dia"] * DIAS_ENTREGA ** 0.5).round().astype(int)
existencia = pd.read_csv(DATA / "lotes.csv").groupby("producto_id")["existencia"].sum()
reorden = reorden.join(existencia).fillna({"existencia": 0})
productos = pd.read_csv(DATA / "productos.csv").set_index("producto_id")
reorden = reorden.join(productos[["nombre", "categoria"]])
por_pedir = reorden[reorden["existencia"] <= reorden["punto_reorden"]].sort_values("demanda_dia", ascending=False)
print(f"\n=== Productos a resurtir hoy (existencia <= punto de reorden): {len(por_pedir)} ===")
print(por_pedir[["nombre", "categoria", "existencia", "punto_reorden"]].head(10).to_string())

# --- 4. Gráficas --------------------------------------------------------------
AZUL, GRIS = "#2a6fdb", "#9aa5b1"

mes = res["Ventas por mes"]
fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(mes["mes"], mes["ventas"] / 1000, color=AZUL, marker="o", label="Ventas")
ax.plot(mes["mes"], mes["utilidad_bruta"] / 1000, color=GRIS, marker="o", label="Utilidad bruta")
ax.set_title("Ventas y utilidad bruta por mes (miles de MXN, datos simulados)")
ax.tick_params(axis="x", rotation=45)
ax.legend(frameon=False)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(IMG / "ventas_mensuales.png", dpi=150)

cat = res["Margen por categoría"].sort_values("margen_pct")
fig, ax = plt.subplots(figsize=(7, 3.5))
ax.barh(cat["categoria"], cat["margen_pct"], color=AZUL)
for y, v in enumerate(cat["margen_pct"]):
    ax.text(v + 0.5, y, f"{v:.0f}%", va="center")
ax.set_title("Margen bruto por categoría (datos simulados)")
ax.set_xlabel("% de margen")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(IMG / "margen_categoria.png", dpi=150)

por_prod = ventas.groupby("producto_id")["venta"].sum().sort_values(ascending=False)
acum = por_prod.cumsum() / por_prod.sum() * 100
fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(range(1, len(acum) + 1), acum.values, color=AZUL)
ax.axhline(80, color=GRIS, linestyle="--", linewidth=1)
n80 = int((acum <= 80).sum())
ax.annotate(f"{n80} de {len(acum)} productos = 80% de la venta", xy=(n80, 80),
            xytext=(n80 + 10, 60), arrowprops={"arrowstyle": "->", "color": GRIS})
ax.set_title("Curva de Pareto (análisis ABC, datos simulados)")
ax.set_xlabel("Productos ordenados por venta")
ax.set_ylabel("% acumulado de la venta")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(IMG / "pareto_abc.png", dpi=150)

print(f"\nGráficas guardadas en {IMG}")
con.close()
