"""Tu tienda Shopify: auditoría y cambios (con confirmación).

Ejemplos: "audita mi tienda", "revisa mi tienda de shopify".
Con Claude: "mejora la descripción del sérum de vitamina C", "pon el labial
rojo a $15.990", "¿qué productos debería arreglar primero?".
"""

from alfred import shopify
from alfred.core import ask_confirmation, command, tool

NO_CONFIG = ("Tu tienda aún no está conectada. Agrega ALFRED_SHOPIFY_STORE y ALFRED_SHOPIFY_TOKEN "
             "a tu archivo .env (ver la guía en el README).")


@command("auditar tienda", [r"\b(?:audita|auditar|auditoria|revisa|revisar|analiza|analizar)\b.*\b(?:tienda|shopify)\b"],
         help="Revisa tu tienda Shopify y genera un Excel con lo que hay que mejorar.",
         examples=["audita mi tienda"], priority=20)
def auditar(ctx, match, texto):
    if not shopify.configured():
        return NO_CONFIG
    resumen, path = shopify.audit(ctx.data_dir / "reportes")
    return f"{resumen}\nDetalle completo en: {path}"


@tool("auditar_tienda_shopify", "Audita todos los productos de la tienda Shopify del usuario y "
      "devuelve un resumen de problemas (imágenes, descripciones, SEO, precios, inventario).", {})
def t_auditar(ctx, args):
    if not shopify.configured():
        return NO_CONFIG
    resumen, path = shopify.audit(ctx.data_dir / "reportes")
    return f"{resumen}\nExcel: {path}"


@tool("buscar_producto_shopify", "Busca productos por nombre y devuelve id, estado, SEO y variantes.",
      {"texto": {"type": "string"}})
def t_buscar(ctx, args):
    if not shopify.configured():
        return NO_CONFIG
    import json
    return json.dumps(shopify.search(args["texto"]), ensure_ascii=False)[:8000] or "Sin resultados."


@tool("actualizar_producto_shopify",
      "Prepara un cambio en un producto de Shopify. NO se aplica hasta que el usuario diga 'sí'. "
      "Usa cadenas vacías para lo que no cambia. El precio se aplica a todas las variantes indicadas.",
      {"producto_id": {"type": "string", "description": "gid://shopify/Product/..."},
       "titulo": {"type": "string"}, "descripcion_html": {"type": "string"},
       "seo_titulo": {"type": "string"}, "seo_descripcion": {"type": "string"},
       "etiquetas": {"type": "string", "description": "Separadas por coma, o vacío."},
       "estado": {"type": "string", "enum": ["", "ACTIVE", "DRAFT", "ARCHIVED"]},
       "precio": {"type": "string", "description": "Nuevo precio en la moneda de la tienda, sin puntos de miles (p. ej. '15990'), o vacío."},
       "variantes_ids": {"type": "array", "items": {"type": "string"},
                         "description": "IDs de variantes para el precio (vacío si no cambia)."}})
def t_actualizar(ctx, args):
    if not shopify.configured():
        return NO_CONFIG
    cambios = {}
    if args.get("titulo"):
        cambios["title"] = args["titulo"]
    if args.get("descripcion_html"):
        cambios["descriptionHtml"] = args["descripcion_html"]
    seo = {k: args[a] for k, a in (("title", "seo_titulo"), ("description", "seo_descripcion")) if args.get(a)}
    if seo:
        cambios["seo"] = seo
    if args.get("etiquetas"):
        cambios["tags"] = [t.strip() for t in args["etiquetas"].split(",") if t.strip()]
    if args.get("estado"):
        cambios["status"] = args["estado"]
    precio, variantes = args.get("precio", ""), args.get("variantes_ids") or []
    if precio and not variantes:
        return "Para cambiar el precio necesito los IDs de las variantes (usa buscar_producto_shopify)."
    if not cambios and not precio:
        return "No indicaste ningún cambio."
    detalle = ", ".join(list(cambios) + ([f"precio → {precio}"] if precio else []))
    return ask_confirmation(
        ctx, f"Cambio preparado en {args['producto_id']}: {detalle}.",
        lambda: shopify.update_product(args["producto_id"], cambios, precio, variantes),
    ) + "\n(Pídele al usuario que diga 'sí' para aplicarlo.)"
