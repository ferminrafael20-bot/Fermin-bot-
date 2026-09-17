# Academia de Tenis - App

App movil (Android/iOS) para una academia de tenis: reservar y pagar clases,
mover una clase ya reservada, anotarse en grupos de entrenamiento, suscribirse
para obtener descuentos, y una tienda con productos traidos desde Mercado Libre.

## Arquitectura

```
tennis-academy-app/
  mobile/       App Expo (React Native + TypeScript)
  admin/        Panel de administracion (React + Vite + TypeScript, web)
  functions/    Backend en Firebase Cloud Functions (Node + TypeScript)
  firestore.rules, firestore.indexes.json, firebase.json
```

- **Autenticacion y base de datos**: Firebase Auth + Firestore.
- **Pagos**: Webpay Plus de Transbank. El SDK de Transbank corre solo en el
  backend (Cloud Functions) porque necesita confirmar ("commit") la transaccion
  con credenciales privadas; el celular nunca ve esas credenciales.
- **Tienda**: un scraper en Cloud Functions trae productos desde paginas de
  busqueda de Mercado Libre (mismo metodo usado antes) y los guarda en
  Firestore. La app solo lee ese catalogo cacheado.

## Modelo de datos (Firestore)

| Coleccion | Contenido |
|---|---|
| `users/{uid}` | perfil, rol (student/coach/admin), estado de suscripcion |
| `classSlots/{id}` | horarios de clase individual abiertos por un profesor |
| `bookings/{id}` | reserva de un usuario sobre un `classSlot` |
| `trainingGroups/{id}` | grupos de entrenamiento (horario fijo, cupos) |
| `subscriptions/{id}` | historial de suscripciones (plan, descuento, vigencia) |
| `payments/{id}` | cada transaccion Webpay (pending/authorized/failed) |
| `affiliatedBrands/{id}` | marcas afiliadas y su codigo/% de descuento |
| `products/{id}` | catalogo cacheado desde Mercado Libre |
| `coaches/{id}` | directorio de profesores (nombre, contacto, especialidad, activo) |

Las reglas de seguridad (`firestore.rules`) impiden que un usuario escriba
directamente su rol, su suscripcion o el resultado de un pago: todo eso lo
escribe el backend con el Admin SDK despues de validar la logica de negocio.

## Puesta en marcha

### 1. Proyecto Firebase
El proyecto ya existe: **`rd-tennis-academy`** (fijado en `.firebaserc`, y sus
claves web ya estan en `mobile/.env.example` / `admin/.env.example`). Si todavia
no hiciste estos pasos en la consola (https://console.firebase.google.com),
hacelos antes de desplegar:
1. **Authentication** → Sign-in method → habilita **Correo/Contrasena**.
2. **Firestore Database** → Crear base de datos → modo produccion → region
   **southamerica-east1** (ya no se puede cambiar si la creaste en otra region).
3. Plan **Blaze** (pago por uso) → requerido para desplegar las Cloud Functions.

Despues, en tu computadora: `npm install -g firebase-tools`, `firebase login`,
y dentro de `tennis-academy-app/` corre `firebase use rd-tennis-academy` (con
`.firebaserc` ya deberia seleccionarse solo).

### 2. Backend (`functions/`)
```bash
cd tennis-academy-app/functions
npm install
cp .env.example .env   # deja WEBPAY_ENV=integration para probar con datos de prueba
npm run build
firebase deploy --only functions,firestore:rules,firestore:indexes
```
Despues del primer deploy, copia la URL publica de la funcion `webpayReturn`
que imprime la CLI y pegala en `functions/.env` como `WEBPAY_RETURN_URL`, luego
vuelve a desplegar (`firebase deploy --only functions`).

Cuando Transbank apruebe tu comercio para produccion, cambia
`WEBPAY_ENV=production` y completa `WEBPAY_COMMERCE_CODE`/`WEBPAY_API_KEY` con
las credenciales reales que te entreguen.

### 3. App movil (`mobile/`)
```bash
cd tennis-academy-app/mobile
npm install
cp .env.example .env   # completa con la config web de tu proyecto Firebase
npx expo start
```
Prueba con Expo Go escaneando el QR, o en un emulador Android/iOS.

### 4. Panel de administracion (`admin/`)
App web separada (no se instala en el celular) para el equipo de la academia.
```bash
cd tennis-academy-app/admin
npm install
cp .env.example .env   # misma config web de Firebase que usaste en mobile/.env
npm run dev             # abre http://localhost:5173
```
Menu lateral colapsable (se puede achicar a solo iconos con el boton ◀/▶):
- **Clases** → submenu *Clases grupales* (`trainingGroups`) y *Clases particulares* (`classSlots`): crear, editar, cancelar o eliminar, asignando un profesor del directorio.
- **Profesores** (sin submenu): alta/edicion/baja del directorio de profesores -- nombre, foto, contacto, especialidad (particulares/grupales/ambas) y activo/inactivo.
- **Tienda**: dispara el scraper de Mercado Libre por termino de busqueda y permite quitar un producto mal traido.
- **Descuentos exclusivos**: alta/edicion/baja de marcas afiliadas (nombre, codigo, % de descuento).
- **Reservas**: listado de todas las reservas con alumno, clase y estado; permite cancelar la reserva de cualquier alumno (por ejemplo, si avisa por telefono).

Solo puede entrar una cuenta cuyo documento `users/{uid}` tenga `role: "admin"` o
`role: "coach"` -- cualquier otra cuenta ve un mensaje de "No autorizado" al
iniciar sesion.

Para publicarlo (Firebase Hosting, gratis para este tamano de trafico):
```bash
npm run build
cd ..
firebase deploy --only hosting
```

### 5. Generar el APK/IPA descargable
Este proyecto usa [EAS Build](https://docs.expo.dev/build/introduction/), que
compila en la nube de Expo (no requiere Android Studio/Xcode instalados):
```bash
npm install -g eas-cli
eas login
eas build:configure         # crea tu projectId de EAS y lo guarda en app.json
eas build --platform android --profile production   # genera el APK/AAB
```
El comando entrega un link de descarga directa del APK al terminar. Para iOS
se necesita una cuenta de Apple Developer.

### 6. Primer usuario administrador
El panel de administracion y la app movil dependen de que exista al menos un
usuario con `role: "admin"`. Para crear el primero:
1. Registrate normalmente desde la app movil (queda con `role: "student"`).
2. Desde la consola de Firestore, edita ese documento en `users/{tuUid}` y
   cambia `role` a `"admin"`.
3. Ya puedes entrar con ese mismo correo al panel de administracion (`admin/`)
   y crear ahi a los profesores, clases, grupos, marcas afiliadas, etc.

## Notas importantes

- **Scraping de Mercado Libre**: es el mismo metodo (parsear el HTML publico
  de resultados de busqueda) que se uso en el proyecto anterior. Es fragil por
  naturaleza -- si Mercado Libre cambia su HTML, `scrapeSearch` en
  `functions/src/scraper.ts` dejara de encontrar productos y hay que ajustar
  los selectores. Ademas, los Terminos de Servicio de Mercado Libre restringen
  el scraping automatizado; si esto se usa en produccion a gran escala, migrar
  a su [API oficial](https://developers.mercadolibre.com.ar) es mas robusto y
  evita bloqueos de IP.
- **Webpay Plus**: mientras no configures credenciales de produccion, todo
  corre contra el ambiente de integracion de Transbank (pagos de prueba, sin
  cobros reales). La confirmacion del pago (`confirmWebpayTransaction`) es la
  unica que activa una reserva, una suscripcion o una membresia de grupo --
  nunca se confia en lo que el celular dice que pago, el monto real se calcula
  siempre en el servidor a partir del precio guardado en Firestore.
- **Cupos "en espera"**: al reservar una clase o anotarse a un grupo, el cupo
  queda retenido por 15 minutos mientras se completa el pago (`pendingHolds` /
  `pendingMemberIds`). Un job programado (`releaseExpiredHolds`) libera esos
  cupos si el usuario abandona el pago sin completarlo.
- Los planes de suscripcion (Basico/Plus/Pro, precio y % de descuento) estan
  definidos en `functions/src/subscriptions.ts` y en
  `mobile/src/screens/subscription/SubscriptionScreen.tsx`, no en Firestore.
  Si se quiere editarlos desde el panel de administracion sin redeployar
  codigo, ese es el siguiente paso natural.
