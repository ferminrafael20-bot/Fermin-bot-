import React, { useEffect, useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, Alert, ActivityIndicator } from 'react-native';
import { collection, onSnapshot, orderBy, query, where } from 'firebase/firestore';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { db } from '@/firebase/config';
import { ClassSlot } from '@/types';
import { bookClass, createWebpayTransaction } from '@/services/api';
import { ClassesStackParamList } from '@/navigation/ClassesNavigator';

type Props = NativeStackScreenProps<ClassesStackParamList, 'ClassesList'>;

export default function ClassesListScreen({ navigation }: Props) {
  const [slots, setSlots] = useState<ClassSlot[]>([]);
  const [loading, setLoading] = useState(true);
  const [bookingId, setBookingId] = useState<string | null>(null);

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

  const handleBook = async (slot: ClassSlot) => {
    setBookingId(slot.id);
    try {
      const { data } = await bookClass({ slotId: slot.id });
      const payment = await createWebpayTransaction({
        purpose: 'class',
        purposeId: data.bookingId,
        amount: slot.price,
      });
      navigation.navigate('WebpayCheckout', {
        url: payment.data.url,
        token: payment.data.token,
        purpose: 'class',
        purposeId: data.bookingId,
      });
    } catch (err: any) {
      Alert.alert('No se pudo reservar', err?.message ?? 'Intenta nuevamente.');
    } finally {
      setBookingId(null);
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
    <View style={styles.container}>
      <TouchableOpacity style={styles.myBookingsButton} onPress={() => navigation.navigate('MyBookings')}>
        <Text style={styles.myBookingsText}>Ver mis clases reservadas</Text>
      </TouchableOpacity>

      <FlatList
        data={slots}
        keyExtractor={(item) => item.id}
        contentContainerStyle={{ padding: 16 }}
        ListEmptyComponent={<Text style={styles.empty}>No hay clases disponibles por ahora.</Text>}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <Text style={styles.title}>{item.title}</Text>
            <Text style={styles.detail}>{item.date} · {item.startTime}-{item.endTime}</Text>
            <Text style={styles.detail}>Profesor: {item.coachName} · Nivel: {item.level}</Text>
            <Text style={styles.detail}>Cupos: {item.bookedBy.length}/{item.capacity}</Text>
            <Text style={styles.price}>${item.price.toLocaleString('es-CL')}</Text>
            <TouchableOpacity
              style={styles.button}
              disabled={bookingId === item.id || item.bookedBy.length >= item.capacity}
              onPress={() => handleBook(item)}
            >
              <Text style={styles.buttonText}>
                {item.bookedBy.length >= item.capacity
                  ? 'Sin cupos'
                  : bookingId === item.id
                  ? 'Reservando...'
                  : 'Reservar y pagar'}
              </Text>
            </TouchableOpacity>
          </View>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  myBookingsButton: { padding: 14, backgroundColor: '#e8f5e9' },
  myBookingsText: { textAlign: 'center', color: '#1b5e20', fontWeight: '600' },
  empty: { textAlign: 'center', color: '#777', marginTop: 40 },
  card: { backgroundColor: '#fff', borderRadius: 12, padding: 16, marginBottom: 14, elevation: 2 },
  title: { fontSize: 16, fontWeight: '700', marginBottom: 4 },
  detail: { fontSize: 13, color: '#555', marginBottom: 2 },
  price: { fontSize: 16, fontWeight: '700', color: '#1b5e20', marginTop: 8, marginBottom: 8 },
  button: { backgroundColor: '#1b5e20', borderRadius: 8, padding: 10 },
  buttonText: { color: '#fff', textAlign: 'center', fontWeight: '600' },
});
