import { onCall, HttpsError } from 'firebase-functions/v2/https';
import { FieldValue } from 'firebase-admin/firestore';
import { db } from './firebaseAdmin';
import { getWebpayTransaction, getWebpayReturnUrl } from './transbank';

type Plan = 'basic' | 'plus' | 'pro';

const PLAN_PRICES: Record<Plan, { price: number; discountPercent: number }> = {
  basic: { price: 9990, discountPercent: 5 },
  plus: { price: 19990, discountPercent: 12 },
  pro: { price: 29990, discountPercent: 20 },
};

export const startSubscription = onCall<{ plan: Plan }>(async (request) => {
  const uid = request.auth?.uid;
  if (!uid) throw new HttpsError('unauthenticated', 'Debes iniciar sesion.');

  const { plan } = request.data;
  const planInfo = PLAN_PRICES[plan];
  if (!planInfo) throw new HttpsError('invalid-argument', 'Plan invalido.');

  const paymentRef = db.collection('payments').doc();
  const buyOrder = paymentRef.id.slice(0, 26);
  const sessionId = uid.slice(0, 61);

  const transaction = getWebpayTransaction();
  const response = await transaction.create(buyOrder, sessionId, planInfo.price, getWebpayReturnUrl());

  await paymentRef.set({
    userId: uid,
    purpose: 'subscription',
    purposeId: plan,
    amount: planInfo.price,
    buyOrder,
    token: response.token,
    status: 'pending',
    createdAt: FieldValue.serverTimestamp(),
  });

  return { token: response.token, url: response.url, paymentId: paymentRef.id };
});

export const cancelSubscription = onCall(async (request) => {
  const uid = request.auth?.uid;
  if (!uid) throw new HttpsError('unauthenticated', 'Debes iniciar sesion.');

  await db.collection('users').doc(uid).update({
    subscriptionActive: false,
  });

  const subsSnap = await db
    .collection('subscriptions')
    .where('userId', '==', uid)
    .where('status', '==', 'active')
    .get();
  await Promise.all(subsSnap.docs.map((d) => d.ref.update({ status: 'cancelled' })));

  return { ok: true };
});

// Usado por confirmWebpayTransaction (webpay.ts) cuando payment.purpose === 'subscription'.
export async function activateSubscription(uid: string, plan: Plan) {
  const planInfo = PLAN_PRICES[plan];
  const now = Date.now();
  const renewalDate = now + 30 * 24 * 60 * 60 * 1000;

  await db.collection('users').doc(uid).update({
    subscriptionActive: true,
    subscriptionPlan: plan,
  });

  await db.collection('subscriptions').add({
    userId: uid,
    plan,
    status: 'active',
    discountPercent: planInfo.discountPercent,
    startDate: now,
    renewalDate,
  });
}
