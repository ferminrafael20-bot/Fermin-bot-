import { httpsCallable } from 'firebase/functions';
import { functions } from '@/firebase/config';
import { PaymentPurpose, SubscriptionPlan, WebpayTransactionResponse } from '@/types';

// --- Reservas de clases ---
export const bookClass = httpsCallable<{ slotId: string }, { bookingId: string }>(
  functions,
  'bookClass'
);

export const moveBooking = httpsCallable<
  { bookingId: string; newSlotId: string },
  { ok: true }
>(functions, 'moveBooking');

export const cancelBooking = httpsCallable<{ bookingId: string }, { ok: true }>(
  functions,
  'cancelBooking'
);

// --- Grupos de entrenamiento ---
export const joinTrainingGroup = httpsCallable<{ groupId: string }, { ok: true }>(
  functions,
  'joinTrainingGroup'
);

export const leaveTrainingGroup = httpsCallable<{ groupId: string }, { ok: true }>(
  functions,
  'leaveTrainingGroup'
);

// --- Suscripciones ---
export const startSubscription = httpsCallable<
  { plan: SubscriptionPlan },
  WebpayTransactionResponse
>(functions, 'startSubscription');

export const cancelSubscription = httpsCallable<Record<string, never>, { ok: true }>(
  functions,
  'cancelSubscription'
);

// --- Pagos via Webpay Plus (Transbank) ---
// purposeId es el id de la reserva, del grupo, o "store" segun corresponda.
export const createWebpayTransaction = httpsCallable<
  { purpose: PaymentPurpose; purposeId: string; amount: number },
  WebpayTransactionResponse
>(functions, 'createWebpayTransaction');

export const confirmWebpayTransaction = httpsCallable<
  { token: string },
  { status: 'AUTHORIZED' | 'FAILED'; purpose: PaymentPurpose; purposeId: string }
>(functions, 'confirmWebpayTransaction');

// --- Tienda / Mercado Libre ---
export const refreshStoreProducts = httpsCallable<{ query: string }, { added: number }>(
  functions,
  'refreshStoreProducts'
);
