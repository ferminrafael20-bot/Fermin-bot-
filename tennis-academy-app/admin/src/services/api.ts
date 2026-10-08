import { httpsCallable } from 'firebase/functions';
import { functions } from '@/firebase/config';

export const refreshStoreProducts = httpsCallable<{ query: string }, { added: number }>(
  functions,
  'refreshStoreProducts'
);

export const adminCancelBooking = httpsCallable<{ bookingId: string }, { ok: true }>(
  functions,
  'adminCancelBooking'
);
