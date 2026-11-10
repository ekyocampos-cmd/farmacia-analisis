"""
Genera datos SIMULADOS de una farmacia independiente pequeña.

No son datos reales de ningún negocio: los nombres de productos son genéricos,
los precios y volúmenes son inventados para que el análisis sea realista sin
exponer información privada.

Salida: productos.csv, ventas.csv, lotes.csv
"""
from pathlib import Path

import numpy as np
import pandas as pd

SEMILLA = 42
INICIO = "2025-11-01"
FIN = "2026-10-31"
CARPETA = Path(__file__).parent

rng = np.random.default_rng(SEMILLA)

# categoría: (num. productos, rango de precio de venta, margen bruto típico)
CATEGORIAS = {
    "Genérico": (45, (25, 180), 0.45),
    "Patente": (30, (120, 900), 0.18),
    "Cuidado personal": (20, (30, 160), 0.35),
    "Dermocosmética": (12, (150, 650), 0.38),
    "Bebé": (13, (40, 420), 0.25),
}

# --- Productos --------------------------------------------------------------
filas = []
pid = 1
for cat, (n, (pmin, pmax), margen) in CATEGORIAS.items():
    for i in range(n):
        precio = round(rng.uniform(pmin, pmax), 0)
        m = np.clip(rng.normal(margen, 0.05), 0.05, 0.7)
        costo = round(precio * (1 - m), 2)
        # popularidad sigue una ley de potencia: pocos productos venden mucho
        popularidad = rng.pareto(1.6) + 0.2
        filas.append({
            "producto_id": pid,
            "nombre": f"{cat[:3].upper()}-{i + 1:03d}",
            "categoria": cat,
            "precio": precio,
            "costo": costo,
            "popularidad": popularidad,
        })
        pid += 1
productos = pd.DataFrame(filas)

# --- Ventas diarias -----------------------------------------------------------
fechas = pd.date_range(INICIO, FIN, freq="D")
dias = len(fechas)
# estacionalidad: temporada de gripa (nov–feb) y fines de semana más flojos
mes = fechas.month.values
factor_temp = np.where(np.isin(mes, [11, 12, 1, 2]), 1.30, 1.0)
factor_dia = np.where(fechas.dayofweek.values == 6, 0.6, 1.0)

pop = productos["popularidad"].values
pop = pop / pop.sum()
VENTAS_DIA_PROMEDIO = 25  # unidades por día, toda la tienda

ventas = []
for d in range(dias):
    lam = VENTAS_DIA_PROMEDIO * factor_temp[d] * factor_dia[d] * pop
    # los genéricos y patente se ven más afectados por la temporada
    unidades = rng.poisson(lam)
    for idx in np.nonzero(unidades)[0]:
        ventas.append((fechas[d].date(), int(productos.at[idx, "producto_id"]), int(unidades[idx])))

ventas = pd.DataFrame(ventas, columns=["fecha", "producto_id", "unidades"])
ventas = ventas.merge(productos[["producto_id", "precio", "costo"]], on="producto_id")
ventas["venta"] = ventas["unidades"] * ventas["precio"]
ventas["costo_total"] = ventas["unidades"] * ventas["costo"]
ventas = ventas[["fecha", "producto_id", "unidades", "venta", "costo_total"]]

# --- Lotes en inventario (con caducidad) -------------------------------------
corte = pd.Timestamp(FIN)
lotes = []
lote_id = 1
for _, p in productos.iterrows():
    for _ in range(rng.integers(1, 3)):
        lotes.append({
            "lote_id": lote_id,
            "producto_id": p["producto_id"],
            "existencia": int(rng.integers(2, 40)),
            "caducidad": (corte + pd.Timedelta(days=int(rng.integers(10, 540)))).date(),
        })
        lote_id += 1
lotes = pd.DataFrame(lotes)

productos.drop(columns="popularidad").to_csv(CARPETA / "productos.csv", index=False)
ventas.to_csv(CARPETA / "ventas.csv", index=False)
lotes.to_csv(CARPETA / "lotes.csv", index=False)
print(f"{len(productos)} productos, {len(ventas)} renglones de venta, {len(lotes)} lotes")
