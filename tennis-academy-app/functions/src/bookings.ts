import { onCall, HttpsError } from 'firebase-functions/v2/https';
import { onSchedule } from 'firebase-functions/v2/scheduler';
import { FieldValue } from 'firebase-admin/firestore';
import { db } from './firebaseAdmin';

const HOLD_DURATION_MS = 15 * 60 * 1000; // tiempo para completar el pago antes de liberar el cupo

export const bookClass = onCall<{ slotId: string }>(async (request) => {
  const uid = request.auth?.uid;
  if (!uid) throw new HttpsError('unauthenticated', 'Debes iniciar sesion.');

  const { slotId } = request.data;
  if (!slotId) throw new HttpsError('invalid-argument', 'Falta el id de la clase.');

  const slotRef = db.collection('classSlots').doc(slotId);
  const bookingRef = db.collection('bookings').doc();

  await db.runTransaction(async (tx) => {
    const slotSnap = await tx.get(slotRef);
    if (!slotSnap.exists) throw new HttpsError('not-found', 'Clase no encontrada.');
    const slot = slotSnap.data() as any;
    if (slot.status === 'cancelled') throw new HttpsError('failed-precondition', 'Esta clase fue cancelada.');

    const pendingHolds = { ...(slot.pendingHolds || {}) };
    const takenCount = (slot.bookedBy || []).length + Object.keys(pendingHolds).length;
    if (takenCount >= slot.capacity) throw new HttpsError('resource-exhausted', 'No quedan cupos para esta clase.');

    pendingHolds[uid] = { bookingId: bookingRef.id, expiresAt: Date.now() + HOLD_DURATION_MS };

    tx.set(bookingRef, {
      userId: uid,
      slotId,
      status: 'pending_payment',
      createdAt: FieldValue.serverTimestamp(),
    });
    tx.update(slotRef, {
      pendingHolds,
      status: takenCount + 1 >= slot.capacity ? 'full' : slot.status,
    });
  });

  return { bookingId: bookingRef.id };
});

export const moveBooking = onCall<{ bookingId: string; newSlotId: string }>(async (request) => {
  const uid = request.auth?.uid;
  if (!uid) throw new HttpsError('unauthenticated', 'Debes iniciar sesion.');

  const { bookingId, newSlotId } = request.data;
  if (!bookingId || !newSlotId) throw new HttpsError('invalid-argument', 'Faltan datos.');

  const bookingRef = db.collection('bookings').doc(bookingId);

  await db.runTransaction(async (tx) => {
    const bookingSnap = await tx.get(bookingRef);
    if (!bookingSnap.exists) throw new HttpsError('not-found', 'Reserva no encontrada.');
    const booking = bookingSnap.data() as any;
    if (booking.userId !== uid) throw new HttpsError('permission-denied', 'Esta reserva no es tuya.');
    if (!['confirmed', 'moved'].includes(booking.status)) {
      throw new HttpsError('failed-precondition', 'Solo puedes mover una clase ya confirmada.');
    }
    if (booking.slotId === newSlotId) return;

    const oldSlotRef = db.collection('classSlots').doc(booking.slotId);
    const newSlotRef = db.collection('classSlots').doc(newSlotId);
    const [oldSlotSnap, newSlotSnap] = await Promise.all([tx.get(oldSlotRef), tx.get(newSlotRef)]);
    if (!newSlotSnap.exists) throw new HttpsError('not-found', 'La nueva clase no existe.');

    const newSlot = newSlotSnap.data() as any;
    const newTakenCount = (newSlot.bookedBy || []).length + Object.keys(newSlot.pendingHolds || {}).length;
    if (newTakenCount >= newSlot.capacity) throw new HttpsError('resource-exhausted', 'Ese horario no tiene cupos.');

    if (oldSlotSnap.exists) {
      const oldSlot = oldSlotSnap.data() as any;
      const bookedBy = (oldSlot.bookedBy || []).filter((id: string) => id !== uid);
      tx.update(oldSlotRef, { bookedBy, status: 'open' });
    }

    const bookedBy = Array.from(new Set([...(newSlot.bookedBy || []), uid]));
    tx.update(newSlotRef, {
      bookedBy,
      status: bookedBy.length >= newSlot.capacity ? 'full' : 'open',
    });
    tx.update(bookingRef, { slotId: newSlotId, status: 'moved' });
  });

  return { ok: true };
});

export const cancelBooking = onCall<{ bookingId: string }>(async (request) => {
  const uid = request.auth?.uid;
  if (!uid) throw new HttpsError('unauthenticated', 'Debes iniciar sesion.');

  const { bookingId } = request.data;
  if (!bookingId) throw new HttpsError('invalid-argument', 'Falta el id de la reserva.');

  const bookingRef = db.collection('bookings').doc(bookingId);

  await db.runTransaction(async (tx) => {
    const bookingSnap = await tx.get(bookingRef);
    if (!bookingSnap.exists) throw new HttpsError('not-found', 'Reserva no encontrada.');
    const booking = bookingSnap.data() as any;
    if (booking.userId !== uid) throw new HttpsError('permission-denied', 'Esta reserva no es tuya.');
    if (booking.status === 'cancelled') return;

    const slotRef = db.collection('classSlots').doc(booking.slotId);
    const slotSnap = await tx.get(slotRef);
    if (slotSnap.exists) {
      const slot = slotSnap.data() as any;
      const pendingHolds = { ...(slot.pendingHolds || {}) };
      delete pendingHolds[uid];
      const bookedBy = (slot.bookedBy || []).filter((id: string) => id !== uid);
      tx.update(slotRef, { pendingHolds, bookedBy, status: 'open' });
    }
    tx.update(bookingRef, { status: 'cancelled' });
  });

  return { ok: true };
});

// Libera cupos "reservados" cuyo pago nunca se completo (usuario abandono el pago).
export const releaseExpiredHolds = onSchedule('every 15 minutes', async () => {
  const now = Date.now();
  const slotsSnap = await db.collection('classSlots').where('status', '!=', 'cancelled').get();

  for (const slotDoc of slotsSnap.docs) {
    const slot = slotDoc.data() as any;
    const pendingHolds = slot.pendingHolds || {};
    const expiredUids = Object.keys(pendingHolds).filter((uid) => pendingHolds[uid].expiresAt < now);
    if (expiredUids.length === 0) continue;

    const remainingHolds = { ...pendingHolds };
    for (const uid of expiredUids) {
      const bookingId = remainingHolds[uid].bookingId;
      delete remainingHolds[uid];
      await db.collection('bookings').doc(bookingId).update({ status: 'cancelled' }).catch(() => undefined);
    }
    await slotDoc.ref.update({ pendingHolds: remainingHolds, status: 'open' });
  }
});
