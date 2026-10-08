import React, { useEffect, useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, Alert, ActivityIndicator } from 'react-native';
import { collection, doc, getDoc, onSnapshot, orderBy, query, where } from 'firebase/firestore';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { db } from '@/firebase/config';
import { useAuth } from '@/context/AuthContext';
import { Booking, ClassSlot } from '@/types';
import { cancelBooking } from '@/services/api';
import { ClassesStackParamList } from '@/navigation/ClassesNavigator';

type Props = NativeStackScreenProps<ClassesStackParamList, 'MyBookings'>;

interface BookingWithSlot extends Booking {
  slot?: ClassSlot;
}

export default function MyBookingsScreen({ navigation }: Props) {
  const { firebaseUser } = useAuth();
  const [bookings, setBookings] = useState<BookingWithSlot[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!firebaseUser) return;
    const q = query(
      collection(db, 'bookings'),
      where('userId', '==', firebaseUser.uid),
      where('status', 'in', ['confirmed', 'moved']),
      orderBy('createdAt', 'desc')
    );
    const unsubscribe = onSnapshot(q, async (snap) => {
      const items = await Promise.all(
        snap.docs.map(async (d) => {
          const booking = { id: d.id, ...d.data() } as Booking;
          const slotSnap = await getDoc(doc(db, 'classSlots', booking.slotId));
          return { ...booking, slot: slotSnap.exists() ? (slotSnap.data() as ClassSlot) : undefined };
        })
      );
      setBookings(items);
      setLoading(false);
    });
    return unsubscribe;
  }, [firebaseUser]);

  const handleCancel = (bookingId: string) => {
    Alert.alert('Cancelar clase', 'Seguro que quieres cancelar esta reserva?', [
      { text: 'No', style: 'cancel' },
      {
        text: 'Si, cancelar',
        style: 'destructive',
        onPress: async () => {
          try {
            await cancelBooking({ bookingId });
          } catch (err: any) {
            Alert.alert('No se pudo cancelar', err?.message ?? 'Intenta nuevamente.');
          }
        },
      },
    ]);
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
      data={bookings}
      keyExtractor={(item) => item.id}
      ListEmptyComponent={<Text style={styles.empty}>Aun no tienes clases reservadas.</Text>}
      renderItem={({ item }) => (
        <View style={styles.card}>
          <Text style={styles.title}>{item.slot?.title ?? 'Clase'}</Text>
          <Text style={styles.detail}>
            {item.slot?.date} · {item.slot?.startTime}-{item.slot?.endTime}
          </Text>
          <View style={styles.row}>
            <TouchableOpacity
              style={[styles.button, styles.secondaryButton]}
              onPress={() => navigation.navigate('MoveBooking', { bookingId: item.id })}
            >
              <Text style={styles.secondaryButtonText}>Mover clase</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.button, styles.dangerButton]}
              onPress={() => handleCancel(item.id)}
            >
              <Text style={styles.buttonText}>Cancelar</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}
    />
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  empty: { textAlign: 'center', color: '#777', marginTop: 40 },
  card: { backgroundColor: '#fff', borderRadius: 12, padding: 16, marginBottom: 14, elevation: 2 },
  title: { fontSize: 16, fontWeight: '700', marginBottom: 4 },
  detail: { fontSize: 13, color: '#555', marginBottom: 10 },
  row: { flexDirection: 'row', gap: 10 },
  button: { flex: 1, borderRadius: 8, padding: 10 },
  secondaryButton: { backgroundColor: '#e8f5e9' },
  secondaryButtonText: { color: '#1b5e20', textAlign: 'center', fontWeight: '600' },
  dangerButton: { backgroundColor: '#b71c1c' },
  buttonText: { color: '#fff', textAlign: 'center', fontWeight: '600' },
});
