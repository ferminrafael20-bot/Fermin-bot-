import React, { useEffect, useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, Alert, ActivityIndicator } from 'react-native';
import { collection, onSnapshot, orderBy, query, where } from 'firebase/firestore';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { db } from '@/firebase/config';
import { ClassSlot } from '@/types';
import { moveBooking } from '@/services/api';
import { ClassesStackParamList } from '@/navigation/ClassesNavigator';

type Props = NativeStackScreenProps<ClassesStackParamList, 'MoveBooking'>;

export default function MoveBookingScreen({ route, navigation }: Props) {
  const { bookingId } = route.params;
  const [slots, setSlots] = useState<ClassSlot[]>([]);
  const [loading, setLoading] = useState(true);
  const [moving, setMoving] = useState<string | null>(null);

  useEffect(() => {
    const q = query(
      collection(db, 'classSlots'),
      where('status', '==', 'open'),
      orderBy('date', 'asc')
    );
    const unsubscribe = onSnapshot(q, (snap) => {
      setSlots(snap.docs.map((d) => ({ id: d.id, ...d.data() } as ClassSlot)));
      setLoading(false);
    });
    return unsubscribe;
  }, []);

  const handleMove = async (newSlotId: string) => {
    setMoving(newSlotId);
    try {
      await moveBooking({ bookingId, newSlotId });
      Alert.alert('Listo', 'Tu clase fue movida correctamente.');
      navigation.goBack();
    } catch (err: any) {
      Alert.alert('No se pudo mover la clase', err?.message ?? 'Intenta nuevamente.');
    } finally {
      setMoving(null);
    }
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#1b5e20" />
      </View>
    );
  }

  return (
    <FlatList
      style={styles.container}
      contentContainerStyle={{ padding: 16 }}
      data={slots}
      keyExtractor={(item) => item.id}
      ListHeaderComponent={<Text style={styles.header}>Elige el nuevo horario para tu clase</Text>}
      ListEmptyComponent={<Text style={styles.empty}>No hay horarios disponibles.</Text>}
      renderItem={({ item }) => (
        <TouchableOpacity
          style={styles.card}
          disabled={moving === item.id || item.bookedBy.length >= item.capacity}
          onPress={() => handleMove(item.id)}
        >
          <Text style={styles.title}>{item.title}</Text>
          <Text style={styles.detail}>{item.date} · {item.startTime}-{item.endTime}</Text>
          <Text style={styles.detail}>Cupos: {item.bookedBy.length}/{item.capacity}</Text>
          <Text style={styles.action}>
            {item.bookedBy.length >= item.capacity ? 'Sin cupos' : moving === item.id ? 'Moviendo...' : 'Elegir este horario'}
          </Text>
        </TouchableOpacity>
      )}
    />
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  header: { fontSize: 15, color: '#555', marginBottom: 12 },
  empty: { textAlign: 'center', color: '#777', marginTop: 40 },
  card: { backgroundColor: '#fff', borderRadius: 12, padding: 16, marginBottom: 14, elevation: 2 },
  title: { fontSize: 16, fontWeight: '700', marginBottom: 4 },
  detail: { fontSize: 13, color: '#555', marginBottom: 2 },
  action: { fontSize: 14, color: '#1b5e20', fontWeight: '600', marginTop: 8 },
});
