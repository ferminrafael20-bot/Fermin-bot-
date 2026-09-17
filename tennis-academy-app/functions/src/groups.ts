import { onCall, HttpsError } from 'firebase-functions/v2/https';
import { db } from './firebaseAdmin';

export const joinTrainingGroup = onCall<{ groupId: string }>(async (request) => {
  const uid = request.auth?.uid;
  if (!uid) throw new HttpsError('unauthenticated', 'Debes iniciar sesion.');

  const { groupId } = request.data;
  if (!groupId) throw new HttpsError('invalid-argument', 'Falta el id del grupo.');

  const groupRef = db.collection('trainingGroups').doc(groupId);

  await db.runTransaction(async (tx) => {
    const groupSnap = await tx.get(groupRef);
    if (!groupSnap.exists) throw new HttpsError('not-found', 'Grupo no encontrado.');
    const group = groupSnap.data() as any;
    const memberIds: string[] = group.memberIds || [];
    const pendingMemberIds: string[] = group.pendingMemberIds || [];

    if (memberIds.includes(uid)) throw new HttpsError('already-exists', 'Ya estas en este grupo.');
    if (memberIds.length + pendingMemberIds.length >= group.capacity) {
      throw new HttpsError('resource-exhausted', 'No quedan cupos en este grupo.');
    }
    if (!pendingMemberIds.includes(uid)) {
      tx.update(groupRef, { pendingMemberIds: [...pendingMemberIds, uid] });
    }
  });

  return { ok: true };
});

export const leaveTrainingGroup = onCall<{ groupId: string }>(async (request) => {
  const uid = request.auth?.uid;
  if (!uid) throw new HttpsError('unauthenticated', 'Debes iniciar sesion.');

  const { groupId } = request.data;
  if (!groupId) throw new HttpsError('invalid-argument', 'Falta el id del grupo.');

  const groupRef = db.collection('trainingGroups').doc(groupId);

  await db.runTransaction(async (tx) => {
    const groupSnap = await tx.get(groupRef);
    if (!groupSnap.exists) return;
    const group = groupSnap.data() as any;
    tx.update(groupRef, {
      memberIds: (group.memberIds || []).filter((id: string) => id !== uid),
      pendingMemberIds: (group.pendingMemberIds || []).filter((id: string) => id !== uid),
    });
  });

  return { ok: true };
});
