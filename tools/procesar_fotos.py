from PIL import Image, ImageOps, ImageFilter
from pathlib import Path
import numpy as np

SRC = Path("/Users/transporteslucasspa/Desktop/PRODUCTOS SOLOS SIN precio")
DST = Path("/Users/transporteslucasspa/Desktop/Transportes Lucas SpA/AUTOMATIZACION 2.0/PROYECTO LOCAS DEL ASEO/web/assets/productos")
LADO = 1000
MARGEN = 1.14   # aire alrededor del producto

# slug -> (archivo, mitad)   mitad: None | "izq" | "der"
MAP = {
    "detergente":                            ("DETERGENTE FUZOL.jpg", None),
    "detergente-2x":                         ("DETERGENTE FUZOL.jpg", None),
    "limpiapisos":                           ("LIMPIAPISOS.jpg", None),
    "limpiavidrios":                         ("VIDRIOS Y ANTIGRASA WYN.jpg", "izq"),
    "antigrasa":                             ("VIDRIOS Y ANTIGRASA WYN.jpg", "der"),
    "wyn-limpiavidrios":                     ("VIDRIOS Y ANTIGRASA WYN.jpg", "izq"),
    "wyn-antigrasa":                         ("VIDRIOS Y ANTIGRASA WYN.jpg", "der"),
    "toalla-swan-70mts":                     ("SWAN GRANDE.jpg", None),
    "cloro-concentrado-impeke":              ("CLORO IMPEKE.jpg", None),
    "prestobarba-3-hojas":                   ("PRESTOBARBA.jpeg", None),
    "alusa-film-20-mts":                     ("FILM PLASTICO CHICO.jpeg", None),
    "glade-flores-tropicales-360":           ("GLADE FLORES TROPICALES.jpeg", None),
    "glade-placer-floral-360":               ("GLADE PLACER FLORAL.jpeg", None),
    "bolsa-basura-optimo-50x70-10-un":       ("BOLSAS DE BASURA.jpeg", None),
    "cif-crema-375-bioactive":               ("CIF CHICO.jpeg", None),
    "cif-crema-750-tradicional":             ("CIF GRANDE.jpeg", None),
    "clorinda-tradicional-1-l":              ("CLORINDA 1LT.jpeg", None),
    "clorinda-cloro-color-930":              ("CLORINDA ROPA COLOR 1LT.jpeg", None),
    "clorox-ropa-colores-vivos-370":         ("ClOROX COLOR CHICO.jpeg", None),
    "desinfectante-igenix-tradicional-360":  ("DESINFECTANTE IGENIX SPRAY.jpeg", None),
    "esponja-acanalada":                     ("ESPONJAS ACANALADAS.jpeg", None),
    "espumita-de-metal-dom":                 ("ESPUMITA ESPONJA 2.jpeg", None),
    "higienico-noble-dh-22-m-6-rollos":      ("NOBLE 22MTS.jpeg", None),
    "ilko-papel-aluminio-7-5-m":             ("ILKO ALUMINIO.jpeg", None),
    "killer-aranas-390":                     ("MATA ARANAS SPRAY.jpeg", None),
    "killer-casa-y-jardin-390":              ("CASA Y JARDIN SPRAY KILLER.jpeg", None),
    "limpiavidrios-wyn-gatillo-750":         ("WYN VIDRIOS GATILLO.jpeg", None),
    "omo-ultra-power-400-doypack":           ("OMO ULTRA POWER DOYPACK.jpeg", None),
    "servilleta-giulietta-coctel-300":       ("SERVILLETAS.jpeg", None),
    "vanish-quitamanchas-rosa-300":          ("VANISH.jpeg", None),
    "shampoo-elvive":                        ("acondicionador elvive.jpg", "izq"),
    "acondicionador-elvive":                 ("acondicionador elvive.jpg", "der"),
    "acondicionador-ballerina-bolsa":        ("ACONDICIONADOR BALLERINA.jpg", None),
    "shampoo-pantene":                       ("ACONDICIONADOR Y SHAMPOOO PANTENE.jpg", "izq"),
    "acondicionador-pantene":                ("ACONDICIONADOR Y SHAMPOOO PANTENE.jpg", "der"),
    "shampoo-sedal":                         ("SHAMPOO Y BALSAMO SEDAL.jpg", "izq"),
    "acondicionador-sedal":                  ("SHAMPOO Y BALSAMO SEDAL.jpg", "der"),
    "esponja-scrup":                         ("SCRUP Y ESPONJA DE PERRO.jpg", "izq"),
    "esponja-pets":                          ("SCRUP Y ESPONJA DE PERRO.jpg", "der"),
    "jabon-popeye":                          ("POPEYE BARRA.jpg", None),
    "toalla-ladysoft-nocturna":              ("TOALLAS HIGIENICAS 2.jpg", "izq"),
    "toalla-ladysoft-dia":                   ("TOALLAS HIGIENICAS 2.jpg", "der"),
    "desodorante-hombre-nivea":              ("DESODORANTES HOMBRE Y MUJER.jpg", "izq"),
    "desodorante-mujer-nivea":               ("DESODORANTES HOMBRE Y MUJER.jpg", "der"),
    "nectar-sprim":                          ("JUGOS EN CAJA SPRIM.jpg", None),
}


def caja_producto(im):
    """Bounding box del producto: lo que se despega del color de la pared."""
    g = np.asarray(im.convert("L").filter(ImageFilter.GaussianBlur(3)), dtype=np.int16)
    h, w = g.shape
    borde = np.concatenate([g[:8].ravel(), g[-8:].ravel(), g[:, :8].ravel(), g[:, -8:].ravel()])
    fondo = np.median(borde)
    mask = np.abs(g - fondo) > 20
    # descarta filas/columnas con casi nada (ruido, sombras)
    cols = np.where(mask.sum(0) > h * 0.02)[0]
    filas = np.where(mask.sum(1) > w * 0.02)[0]
    if len(cols) < 2 or len(filas) < 2:
        return (0, 0, w, h)
    return (int(cols[0]), int(filas[0]), int(cols[-1]) + 1, int(filas[-1]) + 1)


DST.mkdir(parents=True, exist_ok=True)
for slug, (nombre, mitad) in MAP.items():
    im = ImageOps.exif_transpose(Image.open(SRC / nombre)).convert("RGB")
    w, h = im.size
    if mitad == "izq":
        im = im.crop((0, 0, int(w * 0.52), h))
    elif mitad == "der":
        im = im.crop((int(w * 0.48), 0, w, h))
    w, h = im.size

    x0, y0, x1, y1 = caja_producto(im)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    lado = int(max(x1 - x0, y1 - y0) * MARGEN)
    lado = min(lado, max(w, h))          # nunca más grande que la foto

    izq, arr = int(cx - lado / 2), int(cy - lado / 2)
    fondo_color = tuple(np.asarray(im).reshape(-1, 3)[:2000].mean(0).astype(int))
    lienzo = Image.new("RGB", (lado, lado), fondo_color)
    lienzo.paste(im, (-izq, -arr))       # rellena con el color de la pared si se sale
    lienzo.resize((LADO, LADO), Image.LANCZOS).save(
        DST / f"{slug}.jpg", "JPEG", quality=82, optimize=True, progressive=True)

print(f"{len(MAP)} fotos regeneradas con encuadre automático")
