/* Las Locas del Aseo — service worker.
   Que la tienda abra al instante y siga abriendo sin señal.

   Dos reglas y nada más:
   · index.html y catalogo.js → primero la red. Así un cambio de precio se ve
     al toque; si no hay señal, se usa la copia guardada.
   · fotos, íconos y fuentes → primero la copia guardada (no cambian nunca).

   Al subir cambios importantes, sube el número de VERSION: eso borra la caché
   vieja de todos los celulares que ya tienen la web instalada. */

const VERSION = "v76";
const CACHE   = `lda-${VERSION}`;

const ESENCIALES = [
  "./",
  "./index.html",
  "./assets/catalogo.js",
  "./manifest.webmanifest",
  "./assets/icon-192.png",
  "./assets/icon-512.png",
];

self.addEventListener("install", e => {
  e.waitUntil(
    caches.open(CACHE)
      // addAll falla entero si un archivo falla: los pedimos uno a uno
      .then(c => Promise.allSettled(ESENCIALES.map(u => c.add(u))))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys()
      .then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

const guardar = (req, res) => {
  if (res && res.ok) {
    const copia = res.clone();
    caches.open(CACHE).then(c => c.put(req, copia));
  }
  return res;
};

self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;

  const url = new URL(req.url);
  // wa.me, Google Fonts CSS y cualquier otro dominio: que pase directo salvo las fuentes
  const esFuente = /fonts\.(googleapis|gstatic)\.com/.test(url.hostname);
  if (url.origin !== location.origin && !esFuente) return;

  const frescoPrimero =
    req.mode === "navigate" ||
    url.pathname.endsWith("catalogo.js") ||
    url.pathname.endsWith("index.html");

  if (frescoPrimero) {
    e.respondWith(
      fetch(req)
        .then(res => guardar(req, res))
        .catch(() => caches.match(req).then(c => c || caches.match("./index.html")))
    );
    return;
  }

  // fotos / íconos / fuentes: se sirve lo guardado y se refresca por detrás
  e.respondWith(
    caches.match(req).then(cache => {
      const red = fetch(req).then(res => guardar(req, res)).catch(() => cache);
      return cache || red;
    })
  );
});
