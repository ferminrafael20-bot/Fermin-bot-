"""Auditoría y cambios en una tienda Shopify mediante la Admin API (GraphQL).

Configura en tu .env:
  ALFRED_SHOPIFY_STORE=mitienda            (lo que va antes de .myshopify.com)
  ALFRED_SHOPIFY_TOKEN=shpat_...           (token de Admin API de una app de tu tienda
                                            con permisos read_products y write_products)
  ALFRED_SHOPIFY_API_VERSION=2026-07       (opcional)
"""

from __future__ import annotations

import json
import os
import re
import urllib.request
from collections import Counter
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

API_VERSION = "2026-07"

PRODUCTS_QUERY = """
query($cursor: String) {
  products(first: 100, after: $cursor) {
    pageInfo { hasNextPage endCursor }
    nodes {
      id title handle status totalInventory descriptionHtml tags
      featuredMedia { id }
      seo { title description }
      variants(first: 50) { nodes { id price compareAtPrice sku } }
    }
  }
}"""

SEARCH_QUERY = """
query($q: String) {
  products(first: 10, query: $q) {
    nodes { id title status totalInventory tags seo { title description }
            variants(first: 10) { nodes { id title price } } }
  }
}"""

UPDATE_MUTATION = """
mutation($product: ProductUpdateInput!) {
  productUpdate(product: $product) { product { id title } userErrors { field message } }
}"""

PRICE_MUTATION = """
mutation($productId: ID!, $variants: [ProductVariantsBulkInput!]!) {
  productVariantsBulkUpdate(productId: $productId, variants: $variants) { userErrors { field message } }
}"""


def configured() -> bool:
    return bool(os.environ.get("ALFRED_SHOPIFY_STORE") and os.environ.get("ALFRED_SHOPIFY_TOKEN"))


def graphql(query: str, variables: dict | None = None) -> dict:
    store = os.environ["ALFRED_SHOPIFY_STORE"].replace(".myshopify.com", "").strip("/ ")
    version = os.environ.get("ALFRED_SHOPIFY_API_VERSION", API_VERSION)
    req = urllib.request.Request(
        f"https://{store}.myshopify.com/admin/api/{version}/graphql.json",
        data=json.dumps({"query": query, "variables": variables or {}}).encode(),
        headers={"Content-Type": "application/json",
                 "X-Shopify-Access-Token": os.environ["ALFRED_SHOPIFY_TOKEN"]})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
    if data.get("errors"):
        raise RuntimeError(f"Shopify: {data['errors']}")
    return data["data"]


def fetch_products() -> list[dict]:
    out, cursor = [], None
    while True:
        page = graphql(PRODUCTS_QUERY, {"cursor": cursor})["products"]
        out += page["nodes"]
        if not page["pageInfo"]["hasNextPage"]:
            return out
        cursor = page["pageInfo"]["endCursor"]


def _texto(html: str | None) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html or "")).strip()


def issues(p: dict) -> list[str]:
    """Problemas de un producto, del más al menos grave."""
    out = []
    activo = p.get("status") == "ACTIVE"
    variantes = (p.get("variants") or {}).get("nodes", [])
    if activo and (p.get("totalInventory") or 0) <= 0:
        out.append("Activo pero sin inventario (no se puede comprar si controlas stock)")
    if any(float(v.get("price") or 0) <= 0 for v in variantes):
        out.append("Tiene una variante con precio 0")
    if not p.get("featuredMedia"):
        out.append("Sin imagen")
    if len(_texto(p.get("descriptionHtml"))) < 80:
        out.append("Descripción muy corta o vacía (menos de 80 caracteres)")
    seo = p.get("seo") or {}
    if not seo.get("description"):
        out.append("Sin meta descripción SEO")
    elif len(seo["description"]) > 160:
        out.append("Meta descripción SEO de más de 160 caracteres")
    if seo.get("title") and len(seo["title"]) > 70:
        out.append("Título SEO de más de 70 caracteres")
    if len(p.get("title", "")) > 70:
        out.append("Título del producto muy largo (más de 70 caracteres)")
    for v in variantes:
        cmp = v.get("compareAtPrice")
        if cmp and float(cmp) <= float(v.get("price") or 0):
            out.append("Precio de comparación menor o igual al precio (la oferta no se ve)")
            break
    if any(not v.get("sku") for v in variantes):
        out.append("Variante sin SKU")
    if not p.get("tags"):
        out.append("Sin etiquetas (dificulta colecciones y filtros)")
    if p.get("status") == "DRAFT":
        out.append("En borrador (no visible en la tienda)")
    return out


def audit(report_dir: Path, products: list[dict] | None = None) -> tuple[str, Path]:
    products = fetch_products() if products is None else products
    filas = [(p, issues(p)) for p in products]
    conteo = Counter(i for _, lista in filas for i in lista)
    con_problemas = [f for f in filas if f[1]]

    wb = Workbook()
    ws = wb.active
    ws.title = "Auditoría"
    ws.append(["Producto", "Estado", "Inventario", "Nº problemas", "Problemas", "ID"])
    for c in ws[1]:
        c.font, c.fill = Font(bold=True, color="FFFFFF"), PatternFill("solid", fgColor="1F4E78")
    for p, lista in sorted(filas, key=lambda f: -len(f[1])):
        ws.append([p["title"], p.get("status"), p.get("totalInventory"), len(lista),
                   "; ".join(lista) or "OK", p["id"]])
    for col, w in zip("ABCDEF", (40, 10, 11, 13, 90, 38)):
        ws.column_dimensions[col].width = w
    rs = wb.create_sheet("Resumen")
    rs.append(["Problema", "Productos afectados"])
    for c in rs[1]:
        c.font = Font(bold=True)
    for problema, n in conteo.most_common():
        rs.append([problema, n])
    rs.column_dimensions["A"].width = 70

    from datetime import date
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / f"auditoria_shopify_{date.today():%Y-%m-%d}.xlsx"
    wb.save(path)

    lineas = [f"Revisé {len(products)} productos: {len(con_problemas)} tienen algo por mejorar."]
    for problema, n in conteo.most_common(6):
        lineas.append(f"  • {problema}: {n}")
    peores = [p["title"] for p, lista in sorted(con_problemas, key=lambda f: -len(f[1]))[:3]]
    if peores:
        lineas.append("Los que más atención necesitan: " + ", ".join(peores) + ".")
    return "\n".join(lineas), path


def search(texto: str) -> list[dict]:
    return graphql(SEARCH_QUERY, {"q": f"title:*{texto}*"})["products"]["nodes"]


def update_product(product_id: str, cambios: dict, precio: str = "", variant_ids=()) -> str:
    hechos = []
    if cambios:
        r = graphql(UPDATE_MUTATION, {"product": {"id": product_id, **cambios}})["productUpdate"]
        if r["userErrors"]:
            raise RuntimeError(r["userErrors"])
        hechos.append("datos del producto")
    if precio:
        r = graphql(PRICE_MUTATION, {"productId": product_id,
                                     "variants": [{"id": v, "price": precio} for v in variant_ids]})
        if r["productVariantsBulkUpdate"]["userErrors"]:
            raise RuntimeError(r["productVariantsBulkUpdate"]["userErrors"])
        hechos.append(f"precio a {precio}")
    return "Actualicé en Shopify: " + ", ".join(hechos) + "." if hechos else "No había cambios."
