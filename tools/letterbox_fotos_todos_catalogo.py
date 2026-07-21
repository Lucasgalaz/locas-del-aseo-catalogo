"""
Letterbox (contain, no crop) de fotos de TODOS EL CATALOGO hacia
web/assets/productos/{slug}.jpg

Reprocesamiento completo (jul-2026): el dueño renombró TODOS los archivos de
TODOS EL CATALOGO con nombres descriptivos y pidió volver a subir TODOS los
productos que tengan foto ahi -- incluyendo los que ya tenian foto de la
tanda vieja (PRODUCTOS SOLOS SIN precio, sin precio, recorte apretado). Toda
foto de esta carpeta que muestre el producto completo + precio REEMPLAZA a
la vieja.

Tecnica (igual que siempre para este lote): estas fotos YA TRAEN el precio
impreso como sticker abajo del producto, asi que NO se recorta apretado (se
arriesga a cortar el sticker). En su lugar: foto COMPLETA encajada (contain)
dentro de un lienzo cuadrado 1000x1000 con relleno de color neutro (el mismo
gris/blanco del fondo de estudio de la propia foto).

Casos con DOS productos y un solo sticker de precio compartido (shampoo +
acondicionador de una misma linea, WYN antigrasa+vidrios, Ladysoft dia+
nocturna, esponjas Scrub+Pets): se parte el area de producto en mitad
izq/der (con leve solape) y se DUPLICA el sticker de precio (recortado una
sola vez de la foto original) al fondo de cada mitad, antes de encajar cada
una en su propio lienzo cuadrado. Se confirmo en catalogo.js que ambos
productos de cada par comparten el mismo precio antes de duplicar.
"""
from PIL import Image, ImageOps
from pathlib import Path
import numpy as np

SRC = Path("/Users/transporteslucasspa/Desktop/TODOS EL CATALOGO")
DST = Path("/Users/transporteslucasspa/Desktop/Transportes Lucas SpA/AUTOMATIZACION 2.0/PROYECTO LOCAS DEL ASEO/web/assets/productos")
LADO = 1000

# Zona del sticker de precio en las fotos combo (fracciones de W,H). Todas
# las fotos combo de este lote son 1170x2080 con el sticker centrado cerca
# del borde inferior -- se usa una caja generosa que lo cubre completo.
STICKER_BOX = (0.22, 0.85, 0.78, 0.975)

# slug -> nombre de archivo origen (foto completa, sin cortar), o
# slug -> (nombre, "izq"|"der", x0, x1) para fotos con dos productos que
# comparten un solo sticker de precio (se parte y se duplica el sticker).
MAP = {
    # --- reemplazos directos (1 producto por foto) ---
    "acondicionador-ballerina-bolsa":        "ACONDICIONADOR BALLERINA BOLSA.jpg",
    "alusa-film-20-mts":                     "ALUSA FILM PLASTICO COCINA.jpg",
    "desengrasante-winnex":                  "ANTIGRASA WINNEX.jpg",
    "antigrasa":                             "FUZOL ANTIGRASA.jpg",
    "limpiavidrios-wyn-gatillo-750":         "WYN SPRAY LIMPIAVIDRIOS.jpg",
    "cif-vidrios-450-doypack":               "LIMPIAVIDRIOS RECARGA.jpg",
    "clorox-ropa-colores-vivos-370":         "CLORINDA COLOR CHICO.jpg",   # foto mal nombrada: es Clorox, no Clorinda
    "clorinda-cloro-color-930":              "CLORINDA ROPA COLOR.jpg",
    "clorinda-tradicional-1-l":              "CLORO VERDE CLORINDA.jpg",
    "confort":                               "CONFORT RENDIPLUS X6.jpg",
    "confort-2x":                            "CONFORT RENDIPLUS X6.jpg",
    "esponja-absorbente-x3":                 "OPTIMO PAÑO ESPONJA X3.jpg",
    "bolsa-basura-optimo-50x70-10-un":       "BOLSA DE BASURA OPTIMO.jpg",
    "cif-crema-375-bioactive":               "CIF CHICO.jpg",
    "cif-crema-750-tradicional":             "CIF GRANDE .jpg",
    "desinfectante-igenix-lavanda-360":      "DESINFECTANTE IGENIX LAVANDA.jpg",
    "desinfectante-igenix-tradicional-360":  "DESINFECTANTE IGENIX TRADICIONAL.jpg",
    "esponja-acanalada":                     "ESPONJA ACANALADA.jpg",
    "servilleta-giulietta-coctel-300":       "GIULLETA SERVILLETA.jpg",
    "killer-casa-y-jardin-390":              "KILLER CASA JARDIN SPRAY.jpg",
    "killer-aranas-390":                     "KILLER MATA ARAÑAS.jpg",
    "limpiapisos":                           "EXCELL LIMPIAPISOS.jpg",
    "detergente":                            "FUZOL DETERGENTE.jpg",
    "detergente-2x":                         "FUZOL DETERGENTE.jpg",
    "detergente-rinso-500ml":                "RINSO DETERGENTE.jpg",
    "ilko-papel-aluminio-7-5-m":             "PAPEL ALUMINIO COCINA.jpg",
    "pano-microfibra-2x":                    "PAÑOS MICROFIBRA.JPG",
    "toallitas-babysec-45-c-tapa":           "TOALLAS HUMEDAS BABYSEC.jpg",
    "lustramuebles":                         "VIRGINIA LUSTRAMUEBLES SPRAY.jpg",
    "cloro-gel-impeke":                      "CLORO GEL IMPEKE.jpg",
    "cloro-concentrado-impeke":              "CLORO IMPEKE.jpg",
    "desodorante-hombre-nivea":              "NIVEA DESODORANTE HOMBRE.JPG",
    "toalla-nova":                           "NOVA CLASICA X3.jpg",
    "omo-ultra-power-400-doypack":           "OMO DETERGENTE DOYPACK 400ML.jpg",
    "pastilla-wc-pato":                      "PASTILLA PATO PURIFIC.jpg",
    "jabon-popeye":                          "POPEYE BARRA.jpg",
    "prestobarba-3-hojas":                   "PRESTOBARBA.jpg",
    "lavalozas-quix":                        "QUIX RECARGA.jpg",
    "nectar-sprim":                          "SPRIM JUGOS EN CAJA.jpg",
    "toalla-swan-70mts":                     "SWAN PAPEL.jpg",
    "trapero-humedo":                        "TRAPEROS HUMEDOS.jpg",
    "vanish-quitamanchas-rosa-300":          "VANISH QUITA MACHAS LIQUIDO.jpg",
    "higienico-noble-dh-22-m-6-rollos":      "NOBLE PAPEL HIGIENICO.jpg",  # dice "22m/Doble Hoja" -> es el DH 22M, no el 23M

    # --- combos: dos productos en una foto, un solo sticker de precio ---
    # (nombre, mitad, x0_frac, x1_frac) -- x0/x1 con leve solape
    "wyn-limpiavidrios":       ("WYN ANTIGRASA Y LIMPIAVIDRIOS.jpg", "izq", 0.0, 0.55),
    "wyn-antigrasa":           ("WYN ANTIGRASA Y LIMPIAVIDRIOS.jpg", "der", 0.45, 1.0),
    "shampoo-pantene":         ("PANTENE SHAMPOO Y BALSAMO.jpg", "izq", 0.0, 0.55),
    "acondicionador-pantene":  ("PANTENE SHAMPOO Y BALSAMO.jpg", "der", 0.45, 1.0),
    "shampoo-sedal":           ("SEDAL SHAMPOO Y BALSAMO.jpg", "izq", 0.0, 0.55),
    "acondicionador-sedal":    ("SEDAL SHAMPOO Y BALSAMO.jpg", "der", 0.45, 1.0),
    "shampoo-elvive":          ("SHAMPOO Y BALSAMO ELVIVE.jpg", "izq", 0.0, 0.55),
    "acondicionador-elvive":   ("SHAMPOO Y BALSAMO ELVIVE.jpg", "der", 0.45, 1.0),
    "toalla-ladysoft-nocturna": ("TOALLAS HIGIENICAS DIA Y NOCHE.jpg", "izq", 0.0, 0.55),
    "toalla-ladysoft-dia":      ("TOALLAS HIGIENICAS DIA Y NOCHE.jpg", "der", 0.45, 1.0),
    "desodorante-mujer-nivea": ("NIVEA DESODORANTE HOMBRE Y MUJER.jpg", "der", 0.50, 1.0),
    "esponja-scrup":           ("ESPONJAS SCRUP.jpg", "izq", 0.0, 0.66),
    "esponja-pets":            ("ESPONJAS SCRUP.jpg", "der", 0.55, 1.0),
}


def color_fondo(im):
    """Color de fondo de estudio: mediana de una franja angosta en las 4 esquinas."""
    arr = np.asarray(im)
    h, w, _ = arr.shape
    m = max(4, int(min(h, w) * 0.02))
    esquinas = np.concatenate([
        arr[:m, :m].reshape(-1, 3),
        arr[:m, -m:].reshape(-1, 3),
        arr[-m:, :m].reshape(-1, 3),
        arr[-m:, -m:].reshape(-1, 3),
    ])
    return tuple(int(x) for x in np.median(esquinas, axis=0))


def letterbox(im, lado=LADO):
    w, h = im.size
    fondo = color_fondo(im)
    escala = lado / max(w, h)
    nw, nh = round(w * escala), round(h * escala)
    im_r = im.resize((nw, nh), Image.LANCZOS)
    lienzo = Image.new("RGB", (lado, lado), fondo)
    ox, oy = (lado - nw) // 2, (lado - nh) // 2
    lienzo.paste(im_r, (ox, oy))
    return lienzo


def build_split(nombre, mitad, x0f, x1f):
    """Recorta la mitad de producto pedida + duplica el sticker de precio
    (recortado una sola vez de la foto completa) debajo, para no perder el
    precio al partir una foto con dos productos."""
    im = ImageOps.exif_transpose(Image.open(SRC / nombre)).convert("RGB")
    w, h = im.size

    sx0, sy0, sx1, sy1 = STICKER_BOX
    sticker = im.crop((int(w * sx0), int(h * sy0), int(w * sx1), int(h * sy1)))

    # el recorte de producto termina antes de sy0 con margen, para no
    # arrastrar restos del sticker original de la foto combo
    producto = im.crop((int(w * x0f), 0, int(w * x1f), int(h * (sy0 - 0.05))))

    # sticker al mismo ancho que el recorte de producto
    pw = producto.size[0]
    sw, sh = sticker.size
    esc = pw / sw
    sticker_r = sticker.resize((pw, round(sh * esc)), Image.LANCZOS)

    fondo = color_fondo(producto)
    gap = max(4, round(producto.size[1] * 0.015))
    total_h = producto.size[1] + gap + sticker_r.size[1]
    compuesto = Image.new("RGB", (pw, total_h), fondo)
    compuesto.paste(producto, (0, 0))
    compuesto.paste(sticker_r, (0, producto.size[1] + gap))
    return compuesto


DST.mkdir(parents=True, exist_ok=True)
hechos = []
for slug, spec in MAP.items():
    if isinstance(spec, tuple):
        nombre, mitad, x0f, x1f = spec
        compuesto = build_split(nombre, mitad, x0f, x1f)
        lienzo = letterbox(compuesto)
    else:
        im = ImageOps.exif_transpose(Image.open(SRC / spec)).convert("RGB")
        lienzo = letterbox(im)
    lienzo.save(DST / f"{slug}.jpg", "JPEG", quality=88, optimize=True, progressive=True)
    hechos.append(slug)

print(f"{len(hechos)} archivos escritos:")
for s in hechos:
    print(" -", s)
