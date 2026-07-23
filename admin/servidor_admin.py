"""
Panel de administración local de Locas del Aseo — editar precios/nombres/
categorías y subir fotos sin tocar código.

Solo corre en el computador (127.0.0.1), no queda expuesto a internet.
No usa librerías externas: todo con la librería estándar de Python + Pillow
(que ya está instalada, la usan los otros scripts de fotos del proyecto).

Se abre haciendo doble clic en ADMIN-CATALOGO.command (en la carpeta de arriba).
"""
import json
import re
import base64
import webbrowser
from pathlib import Path
from io import BytesIO
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from PIL import Image, ImageOps
import numpy as np

PUERTO = 8765

RAIZ        = Path(__file__).resolve().parent.parent
WEB         = RAIZ / "web"
CATALOGO_JS = WEB / "assets" / "catalogo.js"
PACKS_JS    = WEB / "assets" / "packs.js"
SW_JS       = WEB / "sw.js"
FOTOS_DIR   = WEB / "assets" / "productos"
ADMIN_DIR   = Path(__file__).resolve().parent

CATEGORIAS = ["Limpieza", "Desinfección", "Papel", "Cuidado personal", "Cocina", "Accesorios"]
LADO_FOTO = 1000


def slugificar(nombre: str) -> str:
    import unicodedata
    s = nombre.lower()
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s


def leer_catalogo():
    texto = CATALOGO_JS.read_text(encoding="utf-8")
    m = re.search(r"const\s+CATALOGO\s*=\s*(\[.*\])\s*;", texto, re.S)
    if not m:
        raise ValueError("No se pudo leer el array CATALOGO de catalogo.js")
    return json.loads(m.group(1))


def escribir_catalogo(productos):
    cuerpo = json.dumps(productos, indent=1, ensure_ascii=False)
    texto = (
        "// Generado desde PEDIDOS-Productos.xlsx. Solo nombre, precio y categoría. "
        "Sin costos, sin stock.\n"
        f"const CATALOGO = {cuerpo};\n"
    )
    CATALOGO_JS.write_text(texto, encoding="utf-8")


def leer_packs():
    if not PACKS_JS.is_file():
        return []
    texto = PACKS_JS.read_text(encoding="utf-8")
    m = re.search(r"const\s+PACKS\s*=\s*(\[.*\])\s*;", texto, re.S)
    if not m:
        raise ValueError("No se pudo leer el array PACKS de packs.js")
    return json.loads(m.group(1))


def escribir_packs(packs):
    cuerpo = json.dumps(packs, indent=1, ensure_ascii=False)
    texto = (
        "// Packs armados a mano. Cada item de \"items\" es {n, q}: n = nombre IDÉNTICO al del "
        "catálogo (catalogo.js), q = cantidad.\n"
        "// Se editan desde el Panel de administración (pestaña \"Packs\"), no a mano.\n"
        f"const PACKS = {cuerpo};\n"
    )
    PACKS_JS.write_text(texto, encoding="utf-8")


def subir_version():
    """Sube el número de VERSION en sw.js para botar la caché vieja del celular."""
    texto = SW_JS.read_text(encoding="utf-8")
    def inc(m):
        return f'const VERSION = "v{int(m.group(1)) + 1}";'
    nuevo = re.sub(r'const VERSION = "v(\d+)";', inc, texto)
    SW_JS.write_text(nuevo, encoding="utf-8")


def color_fondo(im):
    arr = np.asarray(im)
    h, w, _ = arr.shape
    m = max(4, int(min(h, w) * 0.02))
    esquinas = np.concatenate([
        arr[:m, :m].reshape(-1, 3), arr[:m, -m:].reshape(-1, 3),
        arr[-m:, :m].reshape(-1, 3), arr[-m:, -m:].reshape(-1, 3),
    ])
    return tuple(int(x) for x in np.median(esquinas, axis=0))


def procesar_y_guardar_foto(slug_id: str, datos: bytes):
    im = ImageOps.exif_transpose(Image.open(BytesIO(datos))).convert("RGB")
    w, h = im.size
    fondo = color_fondo(im)
    escala = LADO_FOTO / max(w, h)
    nw, nh = round(w * escala), round(h * escala)
    im_r = im.resize((nw, nh), Image.LANCZOS)
    lienzo = Image.new("RGB", (LADO_FOTO, LADO_FOTO), fondo)
    lienzo.paste(im_r, ((LADO_FOTO - nw) // 2, (LADO_FOTO - nh) // 2))
    FOTOS_DIR.mkdir(parents=True, exist_ok=True)
    destino = FOTOS_DIR / f"{slug_id}.jpg"
    lienzo.save(destino, "JPEG", quality=88, optimize=True, progressive=True)
    return destino


MIME = {".html": "text/html; charset=utf-8", ".js": "application/javascript; charset=utf-8",
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".json": "application/json"}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # consola limpia

    def _json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _archivo(self, ruta: Path):
        if not ruta.is_file():
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", MIME.get(ruta.suffix, "application/octet-stream"))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(ruta.read_bytes())

    def do_GET(self):
        ruta = urlparse(self.path).path
        if ruta in ("/", "/admin.html"):
            self._archivo(ADMIN_DIR / "admin.html")
        elif ruta == "/api/productos":
            try:
                productos = leer_catalogo()
            except Exception as e:
                self._json({"error": str(e)}, 500)
                return
            fotos = {p.stem for p in FOTOS_DIR.glob("*.jpg")} if FOTOS_DIR.is_dir() else set()
            self._json({"productos": productos, "categorias": CATEGORIAS, "fotos": sorted(fotos)})
        elif ruta == "/api/packs":
            try:
                packs = leer_packs()
            except Exception as e:
                self._json({"error": str(e)}, 500)
                return
            self._json({"packs": packs})
        elif ruta.startswith("/assets/"):
            objetivo = (WEB / ruta.lstrip("/")).resolve()
            if WEB.resolve() in objetivo.parents:
                self._archivo(objetivo)
            else:
                self.send_error(403)
        else:
            self.send_error(404)

    def do_POST(self):
        ruta = urlparse(self.path).path
        largo = int(self.headers.get("Content-Length", 0))
        crudo = self.rfile.read(largo) if largo else b"{}"
        try:
            cuerpo = json.loads(crudo.decode("utf-8"))
        except Exception:
            self._json({"error": "JSON inválido"}, 400)
            return

        if ruta == "/api/guardar":
            productos = cuerpo.get("productos", [])
            limpios = []
            for p in productos:
                nombre = str(p.get("n", "")).strip()
                if not nombre:
                    continue
                try:
                    precio = int(round(float(p.get("p", 0))))
                except (TypeError, ValueError):
                    precio = 0
                categoria = str(p.get("c", "")).strip() or "Limpieza"
                producto = {"n": nombre, "p": precio, "c": categoria}
                of = p.get("of")
                if isinstance(of, dict) and of.get("q") and of.get("p") is not None:
                    try:
                        producto["of"] = {"q": int(round(float(of["q"]))), "p": int(round(float(of["p"])))}
                    except (TypeError, ValueError):
                        pass
                limpios.append(producto)
            try:
                escribir_catalogo(limpios)
                subir_version()
            except Exception as e:
                self._json({"error": str(e)}, 500)
                return
            self._json({"ok": True, "total": len(limpios)})

        elif ruta == "/api/foto":
            nombre = str(cuerpo.get("nombre", "")).strip()
            b64 = cuerpo.get("imagen_base64", "")
            if not nombre or not b64:
                self._json({"error": "Falta nombre o imagen"}, 400)
                return
            if "," in b64:
                b64 = b64.split(",", 1)[1]
            try:
                datos = base64.b64decode(b64)
                sid = slugificar(nombre)
                procesar_y_guardar_foto(sid, datos)
                subir_version()
            except Exception as e:
                self._json({"error": str(e)}, 500)
                return
            self._json({"ok": True, "slug": sid})

        elif ruta == "/api/packs/guardar":
            packs = cuerpo.get("packs", [])
            limpios = []
            for pk in packs:
                nombre = str(pk.get("n", "")).strip()
                if not nombre:
                    continue
                emoji = str(pk.get("e", "")).strip() or "🧴"
                desc = str(pk.get("d", "")).strip()
                items, vistos = [], set()
                for it in pk.get("items", []):
                    if isinstance(it, dict):
                        n = str(it.get("n", "")).strip()
                        try:
                            q = int(round(float(it.get("q", 1))))
                        except (TypeError, ValueError):
                            q = 1
                    else:
                        n, q = str(it).strip(), 1
                    if not n or n in vistos:
                        continue
                    vistos.add(n)
                    items.append({"n": n, "q": max(1, q)})
                limpios.append({"e": emoji, "n": nombre, "d": desc, "items": items})
            try:
                escribir_packs(limpios)
                subir_version()
            except Exception as e:
                self._json({"error": str(e)}, 500)
                return
            self._json({"ok": True, "total": len(limpios)})

        elif ruta == "/api/foto/borrar":
            nombre = str(cuerpo.get("nombre", "")).strip()
            sid = slugificar(nombre)
            destino = FOTOS_DIR / f"{sid}.jpg"
            if destino.is_file():
                destino.unlink()
            try:
                subir_version()
            except Exception:
                pass
            self._json({"ok": True})

        else:
            self.send_error(404)


def main():
    servidor = ThreadingHTTPServer(("127.0.0.1", PUERTO), Handler)
    url = f"http://127.0.0.1:{PUERTO}/"
    print(f"Panel de administración corriendo en {url}")
    print("Deja esta ventana abierta mientras usas el panel. Ctrl+C para cerrar.")
    webbrowser.open(url)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
