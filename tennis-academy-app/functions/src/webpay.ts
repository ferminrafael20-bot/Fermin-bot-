import { onCall, HttpsError, onRequest } from 'firebase-functions/v2/https';
import { logger } from 'firebase-functions';
import { db } from './firebaseAdmin';
import { FieldValue } from 'firebase-admin/firestore';
import { activateSubscription } from './subscriptions';
import { getWebpayTransaction, getWebpayReturnUrl } from './transbank';

type Purpose = 'class' | 'group' | 'store' | 'subscription';

// Calcula el monto real a cobrar en el servidor -- nunca se confia en un monto
// enviado por el cliente, para evitar que alguien pague menos de lo debido.
async function resolveAmount(
  purpose: Purpose,
  purposeId: string,
  uid: string
): Promise<number> {
  if (purpose === 'class') {
    const bookingSnap = await db.collection('bookings').doc(purposeId).get();
    if (!bookingSnap.exists) throw new HttpsError('not-found', 'Reserva no encontrada.');
    const booking = bookingSnap.data() as any;
    if (booking.userId !== uid) throw new HttpsError('permission-denied', 'Esta reserva no es tuya.');
    const slotSnap = await db.collection('classSlots').doc(booking.slotId).get();
    if (!slotSnap.exists) throw new HttpsError('not-found', 'Clase no encontrada.');
    return (slotSnap.data() as any).price;
  }
  if (purpose === 'group') {
    const groupSnap = await db.collection('trainingGroups').doc(purposeId).get();
    if (!groupSnap.exists) throw new HttpsError('not-found', 'Grupo no encontrado.');
    return (groupSnap.data() as any).monthlyPrice;
  }
  if (purpose === 'store') {
    const productSnap = await db.collection('products').doc(purposeId).get();
    if (!productSnap.exists) throw new HttpsError('not-found', 'Producto no encontrado.');
    return Math.round((productSnap.data() as any).price);
  }
  throw new HttpsError('invalid-argument', 'Proposito de pago invalido.');
}

export const createWebpayTransaction = onCall<{ purpose: Purpose; purposeId: string }>(
  async (request) => {
    const uid = request.auth?.uid;
    if (!uid) throw new HttpsError('unauthenticated', 'Debes iniciar sesion.');

    const { purpose, purposeId } = request.data;
    if (!purpose || !purposeId) throw new HttpsError('invalid-argument', 'Faltan datos del pago.');

    const amount = await resolveAmount(purpose, purposeId, uid);
    const paymentRef = db.collection('payments').doc();
    const buyOrder = paymentRef.id.slice(0, 26); // Transbank limita buyOrder a 26 caracteres
    const sessionId = uid.slice(0, 61);

    const transaction = getWebpayTransaction();
    const response = await transaction.create(buyOrder, sessionId, amount, getWebpayReturnUrl());

    await paymentRef.set({
      userId: uid,
      purpose,
      purposeId,
      amount,
      buyOrder,
      token: response.token,
      status: 'pending',
      createdAt: FieldValue.serverTimestamp(),
    });

    return { token: response.token, url: response.url, paymentId: paymentRef.id };
  }
);

export const confirmWebpayTransaction = onCall<{ token: string }>(async (request) => {
  const uid = request.auth?.uid;
  if (!uid) throw new HttpsError('unauthenticated', 'Debes iniciar sesion.');

  const { token } = request.data;
  if (!token) throw new HttpsError('invalid-argument', 'Falta el token de la transaccion.');

  const paymentQuery = await db.collection('payments').where('token', '==', token).limit(1).get();
  if (paymentQuery.empty) throw new HttpsError('not-found', 'Pago no encontrado.');
  const paymentDoc = paymentQuery.docs[0];
  const payment = paymentDoc.data() as any;
  if (payment.userId !== uid) throw new HttpsError('permission-denied', 'Este pago no es tuyo.');

  const transaction = getWebpayTransaction();
  let commitStatus: 'AUTHORIZED' | 'FAILED' = 'FAILED';
  try {
    const commitResponse = await transaction.commit(token);
    commitStatus = commitResponse.status === 'AUTHORIZED' ? 'AUTHORIZED' : 'FAILED';
  } catch (err) {
    logger.error('Error al confirmar transaccion Webpay', err);
    commitStatus = 'FAILED';
  }

  await paymentDoc.ref.update({
    status: commitStatus === 'AUTHORIZED' ? 'authorized' : 'failed',
    confirmedAt: FieldValue.serverTimestamp(),
  });

  await applyPaymentOutcome(payment.purpose, payment.purposeId, uid, commitStatus === 'AUTHORIZED');

  return { status: commitStatus, purpose: payment.purpose, purposeId: payment.purposeId };
});

async function applyPaymentOutcome(
  purpose: Purpose,
  purposeId: string,
  uid: string,
  authorized: boolean
) {
  if (purpose === 'class') {
    const bookingRef = db.collection('bookings').doc(purposeId);
    await db.runTransaction(async (tx) => {
      const bookingSnap = await tx.get(bookingRef);
      if (!bookingSnap.exists) return;
      const booking = bookingSnap.data() as any;
      const slotRef = db.collection('classSlots').doc(booking.slotId);
      const slotSnap = await tx.get(slotRef);
      if (!slotSnap.exists) return;
      const slot = slotSnap.data() as any;
      const pendingHolds = { ...(slot.pendingHolds || {}) };
      delete pendingHolds[uid];

      if (authorized) {
        const bookedBy = Array.from(new Set([...(slot.bookedBy || []), uid]));
        tx.update(slotRef, {
          pendingHolds,
          bookedBy,
          status: bookedBy.length >= slot.capacity ? 'full' : 'open',
        });
        tx.update(bookingRef, { status: 'confirmed', paymentId: purposeId });
      } else {
        tx.update(slotRef, { pendingHolds, status: 'open' });
        tx.update(bookingRef, { status: 'cancelled' });
      }
    });
  } else if (purpose === 'group') {
    const groupRef = db.collection('trainingGroups').doc(purposeId);
    await db.runTransaction(async (tx) => {
      const groupSnap = await tx.get(groupRef);
      if (!groupSnap.exists) return;
      const group = groupSnap.data() as any;
      const pendingMemberIds = (group.pendingMemberIds || []).filter((id: string) => id !== uid);
      if (authorized) {
        const memberIds = Array.from(new Set([...(group.memberIds || []), uid]));
        tx.update(groupRef, { memberIds, pendingMemberIds });
      } else {
        tx.update(groupRef, { pendingMemberIds });
      }
    });
  } else if (purpose === 'store') {
    // Los pagos de tienda no bloquean stock propio (el stock real vive en Mercado Libre);
    // solo dejamos registro del pago para que la academia gestione el envio manualmente.
    logger.info(`Pago de tienda ${authorized ? 'autorizado' : 'fallido'} para producto ${purposeId} de ${uid}`);
  } else if (purpose === 'subscription' && authorized) {
    await activateSubscription(uid, purposeId as 'basic' | 'plus' | 'pro');
  }
}

// Punto de retorno publico que Transbank llama por POST luego de que el usuario paga.
// Redirige al esquema propio de la app para que el WebView del checkout lo intercepte
// (ver mobile/src/screens/payment/WebpayCheckoutScreen.tsx).
export const webpayReturn = onRequest((req, res) => {
  const tokenWs = (req.body?.token_ws || req.query?.token_ws || '') as string;
  const redirectUrl = `academiatenis://webpay-return?token_ws=${encodeURIComponent(tokenWs)}`;
  res.set('Content-Type', 'text/html');
  res.send(`<!DOCTYPE html><html><body onload="location.href='${redirectUrl}'">
    Redirigiendo a la app... <a href="${redirectUrl}">Toca aqui si no vuelves automaticamente</a>
  </body></html>`);
});
