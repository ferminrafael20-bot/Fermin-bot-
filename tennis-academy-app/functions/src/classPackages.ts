import { onCall, HttpsError } from 'firebase-functions/v2/https';
import { FieldValue } from 'firebase-admin/firestore';
import { db } from './firebaseAdmin';
import { getWebpayTransaction, getWebpayReturnUrl } from './transbank';

const DAY_MS = 24 * 60 * 60 * 1000;

// Compra de un paquete de clases (p.ej. "Pack 4 clases"). No bloquea ningun cupo --
// a diferencia de reservar una clase o anotarse a un grupo, comprar un paquete no
// consume ningun recurso escaso, asi que no hace falta un "hold": el paquete recien
// se crea (en activateClassPackage) cuando Transbank confirma el pago.
export const purchaseClassPackage = onCall<{ packageId: string }>(async (request) => {
  const uid = request.auth?.uid;
  if (!uid) throw new HttpsError('unauthenticated', 'Debes iniciar sesion.');

  const { packageId } = request.data;
  if (!packageId) throw new HttpsError('invalid-argument', 'Falta el paquete a comprar.');

  const packageSnap = await db.collection('classPackages').doc(packageId).get();
  if (!packageSnap.exists) throw new HttpsError('not-found', 'Paquete no encontrado.');
  const pkg = packageSnap.data() as any;
  if (pkg.active === false) throw new HttpsError('failed-precondition', 'Este paquete ya no esta disponible.');

  const paymentRef = db.collection('payments').doc();
  const buyOrder = paymentRef.id.slice(0, 26); // Transbank limita buyOrder a 26 caracteres
  const sessionId = uid.slice(0, 61);

  const transaction = getWebpayTransaction();
  const response = await transaction.create(buyOrder, sessionId, pkg.price, getWebpayReturnUrl());

  await paymentRef.set({
    userId: uid,
    purpose: 'classPackage',
    purposeId: packageId,
    amount: pkg.price,
    buyOrder,
    token: response.token,
    status: 'pending',
    createdAt: FieldValue.serverTimestamp(),
  });

  return { token: response.token, url: response.url, paymentId: paymentRef.id };
});

// Usado por applyPaymentOutcome (webpay.ts) cuando payment.purpose === 'classPackage' y
// Transbank autorizo el pago. Crea el paquete del alumno con sus creditos disponibles.
export async function activateClassPackage(uid: string, packageId: string, paymentId: string) {
  const packageSnap = await db.collection('classPackages').doc(packageId).get();
  if (!packageSnap.exists) return;
  const pkg = packageSnap.data() as any;
  const now = Date.now();

  await db.collection('userPackages').add({
    userId: uid,
    packageId,
    packageName: pkg.name,
    totalClasses: pkg.classCount,
    usedClasses: 0,
    remainingClasses: pkg.classCount,
    purchasedAt: now,
    expiresAt: now + pkg.validityDays * DAY_MS,
    status: 'active',
    paymentId,
  });
}

// Agenda una clase ya existente (abierta por un profesor) usando un credito de un
// paquete ya pagado -- no pasa por Webpay de nuevo, el pago ya se hizo al comprar el
// paquete. El calendario de dias/horarios disponibles en la app es simplemente el
// listado de classSlots abiertos, agrupado por fecha.
export const scheduleClassFromPackage = onCall<{ userPackageId: string; slotId: string }>(
  async (request) => {
    const uid = request.auth?.uid;
    if (!uid) throw new HttpsError('unauthenticated', 'Debes iniciar sesion.');

    const { userPackageId, slotId } = request.data;
    if (!userPackageId || !slotId) throw new HttpsError('invalid-argument', 'Faltan datos.');

    const userPackageRef = db.collection('userPackages').doc(userPackageId);
    const slotRef = db.collection('classSlots').doc(slotId);
    const bookingRef = db.collection('bookings').doc();

    await db.runTransaction(async (tx) => {
      const [userPackageSnap, slotSnap] = await Promise.all([tx.get(userPackageRef), tx.get(slotRef)]);

      if (!userPackageSnap.exists) throw new HttpsError('not-found', 'Paquete no encontrado.');
      const userPackage = userPackageSnap.data() as any;
      if (userPackage.userId !== uid) throw new HttpsError('permission-denied', 'Este paquete no es tuyo.');
      if (userPackage.status !== 'active') {
        throw new HttpsError('failed-precondition', 'Este paquete ya no esta activo.');
      }
      if (userPackage.remainingClasses <= 0) {
        throw new HttpsError('failed-precondition', 'No te quedan clases disponibles en este paquete.');
      }
      if (userPackage.expiresAt < Date.now()) {
        throw new HttpsError('failed-precondition', 'Este paquete ya vencio.');
      }

      if (!slotSnap.exists) throw new HttpsError('not-found', 'Clase no encontrada.');
      const slot = slotSnap.data() as any;
      if (slot.status === 'cancelled') throw new HttpsError('failed-precondition', 'Esta clase fue cancelada.');
      const takenCount = (slot.bookedBy || []).length + Object.keys(slot.pendingHolds || {}).length;
      if (takenCount >= slot.capacity) throw new HttpsError('resource-exhausted', 'No quedan cupos para esta clase.');

      const bookedBy = Array.from(new Set([...(slot.bookedBy || []), uid]));
      tx.update(slotRef, {
        bookedBy,
        status: bookedBy.length >= slot.capacity ? 'full' : slot.status,
      });

      tx.set(bookingRef, {
        userId: uid,
        slotId,
        status: 'confirmed',
        packageId: userPackageId,
        createdAt: FieldValue.serverTimestamp(),
      });

      const remainingClasses = userPackage.remainingClasses - 1;
      tx.update(userPackageRef, {
        remainingClasses,
        usedClasses: (userPackage.usedClasses || 0) + 1,
        status: remainingClasses <= 0 ? 'completed' : 'active',
      });
    });

    return { bookingId: bookingRef.id };
  }
);
