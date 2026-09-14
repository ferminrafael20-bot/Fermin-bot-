import { useEffect, useState } from 'react';
import { collection, onSnapshot } from 'firebase/firestore';
import { db } from '@/firebase/config';
import { Coach } from '@/types';

export function useCoaches() {
  const [coaches, setCoaches] = useState<Coach[]>([]);

  useEffect(() => {
    const unsubscribe = onSnapshot(collection(db, 'coaches'), (snap) => {
      setCoaches(snap.docs.map((d) => ({ id: d.id, ...d.data() } as Coach)));
    });
    return unsubscribe;
  }, []);

  return coaches;
}
