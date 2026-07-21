# Locas del Aseo — tienda web

Sitio estático (un solo HTML). Sin servidor, sin base de datos, sin login.
No hay nada "adentro" que hackear y no tiene ninguna conexión al Excel.

**Versión actual: v6 "Mercado" (13/07/2026).** La versión anterior (glass rosado)
quedó guardada en `_versiones_descartadas/index_v5_aurora_2026-07-13.html`: si algo
de lo nuevo no gusta, se vuelve copiando ese archivo sobre `index.html`.

## Archivos

```
index.html                    ← el sitio completo
manifest.webmanifest          ← para que se instale como app en el celular
sw.js                         ← hace que abra al instante y funcione sin señal
assets/catalogo.js            ← 64 productos: nombre, precio, categoría
assets/productos/             ← fotos (una por producto, nombre exacto)
assets/productos/NOMBRES DE FOTOS.txt  ← la lista de nombres a usar
assets/icon-*.png             ← ícono de la app (burbuja rosada, provisorio)
```

## Fotos

Deja cada foto en `assets/productos/` con el nombre de archivo que dice
`NOMBRES DE FOTOS.txt`. Ejemplo: `detergente.jpg`, `cloro-gel-impeke.jpg`.

- Formato `.jpg`, cuadrada (1:1) idealmente.
- **Sin el precio encima.** El precio lo pone la web sola.
- El producto que no tenga foto muestra una tarjeta de color con ícono. No se rompe.

## Cambiar precios o productos

**Forma fácil (recomendada):** doble clic en `ADMIN-CATALOGO-ASEO.command`
(hay una copia en el Escritorio y otra en la carpeta del proyecto, junto a
este README). Abre un panel en el navegador donde puedes editar nombre,
precio y categoría de cada producto, agregar productos nuevos, subir/cambiar
la foto de cualquiera con un click, y borrar los que ya no vendes. Al guardar,
escribe directo en `assets/catalogo.js` y sube la versión de `sw.js` solo.
Deja la ventana de Terminal abierta mientras lo usas; ciérrala cuando termines.
Corre solo en tu computador (127.0.0.1), no queda expuesto a internet.

**Forma manual:** se editan directo en `assets/catalogo.js`. Se pueden
regenerar desde el Excel con el script que dejó Claude (lee
`PEDIDOS-Productos.xlsx` y exporta **solo nombre, precio y categoría** —
nunca los costos ni el stock).

## Ajustes del negocio

Al final de `index.html`, en el bloque `AJUSTES DEL NEGOCIO`:

| Variable | Qué es | Ahora |
|---|---|---|
| `WHATSAPP` | número que recibe los pedidos | 56956615153 |
| `ENVIO_MIN` | compra mínima para despacho gratis | $15.000 |
| `ENVIO_COSTO` | cobro bajo el mínimo | $2.000 |
| `COMUNAS` | comunas con reparto | Peñalolén, Macul, Ñuñoa, La Reina, La Florida |
| `CORTE_HORA` | hasta qué hora se pide para que llegue hoy | 18 |
| `DIAS_REPARTO` | días que se reparte (0=domingo … 6=sábado) | lunes a sábado |
| `PAGOS` | formas de pago que ofrece el carro | Efectivo, Transferencia |
| `MAS_PEDIDOS` | los que llevan etiqueta 🔥 y arman el riel "Los más pedidos" | 12 productos |
| `VITRINA` | las 3 tarjetas que rotan en el hero | despacho, entrega, pack |
| `FAQ` | las preguntas frecuentes | 6 preguntas |
| `PACKS` | los packs armados | 4 packs |
| `INFALTABLES` | lo que se ofrece en el carro si no va en el pedido | 5 productos |

## Lo que trae la v6 (además de lo de antes)

- **Buscador con sugerencias.** Escribe y aparecen los productos con foto y precio;
  se puede navegar con las flechas y entrar con Enter. Atajo: tecla `/`.
- **Barra de categorías fija** con el conteo de productos de cada una.
- **Vitrina en el hero**: 3 tarjetas que rotan solas cada 6 segundos.
- **Riel "Los más pedidos"**: se arrastra con el mouse o el dedo, con flechas.
- **Filtros de verdad**: orden (recomendados / precio / A-Z), tope de precio,
  "solo con foto" y "solo favoritos". El catálogo carga de a 24 con "Ver más".
- **Favoritos** con corazón, guardados en el teléfono.
- **Packs con las fotos** de los productos que traen adentro.
- **Zona de reparto interactiva**: elige la comuna y dice si le llega hoy.
- **Preguntas frecuentes** en acordeón.
- **Detalles vivos**: el producto vuela al carro al agregarlo, avisos (toast),
  burbujas que estallan al agregar un pack, barra de progreso de scroll,
  contadores que suben solos y **tres temas** (rosado → celeste → verde).
- **Forma de pago** (efectivo o transferencia): se elige en el carro y va escrita
  en el mensaje de WhatsApp.

## Lo que hace la web sola

**Reloj de entrega.** En el hero y en el carro va contando: *"Pide en 2h 14m y te
llega hoy"*. Pasada `CORTE_HORA` (o si hoy no se reparte según `DIAS_REPARTO`)
cambia solo a *"llega mañana temprano"*. **Confirma que los días y la hora estén
bien**, porque la web lo está prometiendo.

**Packs.** Los nombres de los productos de cada pack tienen que ser idénticos a
los del catálogo. Si el Excel deja de traer uno, el pack se arma igual con el
resto y avisa en la consola del navegador. El precio se suma solo, sin descuento:
el gancho es la comodidad y que el Pack Casa Completa pasa los $15.000, así que
va con despacho gratis. Si se les quiere dar descuento, hay que decidirlo con
Felix, porque toca el margen.

| Pack | Productos | Precio |
|---|---|---|
| Casa Completa | 11 | $15.600 (con despacho gratis) |
| Baño | 6 | $8.940 |
| Lavandería | 4 | $10.000 |
| Cocina | 7 | $6.990 |

**Cerrar la brecha del despacho gratis.** Si le faltan $500, el carro le ofrece un
producto de exactamente $500 y le dice que así el despacho le sale gratis. Solo
lo ofrece cuando es cierto: si ningún producto por sí solo alcanza a cerrar la
brecha, no promete nada.

**Volver a pedir.** Al enviar el pedido por WhatsApp se guarda una copia en el
teléfono del cliente. La próxima vez que entre, lo primero que ve es *"Pediste
hace una semana · 4 productos · $12.100"* y un botón para rearmar el carro igual.
Los precios se toman siempre del catálogo de hoy, nunca los del pedido viejo.

**Se instala como app.** El celular ofrece dejarla en la pantalla de inicio. Queda
con ícono propio, abre sin barra del navegador y funciona sin señal (el catálogo
queda guardado). En iPhone hay que hacerlo a mano: Compartir → Agregar a inicio,
y la web se lo explica.

**Ficha del producto.** Al tocar la foto o el nombre se abre grande, con zoom, el
precio, el botón de agregar y otros productos del mismo tipo.

## Al subir cambios

Si tocas `index.html`, `catalogo.js` o los precios, **sube el número de `VERSION`
en `sw.js`** (`v1` → `v2`). Eso bota la copia guardada en los celulares que ya
tienen la web instalada; si no, pueden seguir viendo la versión vieja.
Si usas el panel (`ADMIN-CATALOGO-ASEO.command`) esto se hace solo, no hay que
tocar nada a mano.

## Publicar (cuando se apruebe)

Mismo stack que transporteslucas.cl: GitHub privado → Vercel (gratis) →
Cloudflare DNS (gratis) → dominio en NIC Chile (~$9.950/año).
Único costo real: el dominio.

Ojo: instalarla como app y el modo sin señal **solo funcionan en HTTPS**. En
Vercel viene por defecto, pero abriendo el archivo con doble clic (`file://`)
no se ven.
