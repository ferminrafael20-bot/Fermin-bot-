import React, { useEffect, useMemo, useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, Alert, ActivityIndicator } from 'react-native';
import { collection, onSnapshot, orderBy, query, where } from 'firebase/firestore';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { db } from '@/firebase/config';
import { ClassSlot } from '@/types';
import { scheduleClassFromPackage } from '@/services/api';
import { ClassesStackParamList } from '@/navigation/ClassesNavigator';

type Props = NativeStackScreenProps<ClassesStackParamList, 'ScheduleFromPackage'>;

const WEEKDAYS = ['dom', 'lun', 'mar', 'mie', 'jue', 'vie', 'sab'];
const MONTHS = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'];

// Evitamos Intl/toLocaleDateString con locale "es-CL": Hermes no siempre trae los
// datos de ese locale embebidos, asi que armamos las etiquetas a mano.
function dayLabel(dateStr: string) {
  const d = new Date(`${dateStr}T00:00:00`);
  return { weekday: WEEKDAYS[d.getDay()], day: d.getDate(), month: MONTHS[d.getMonth()] };
}

export default function ScheduleFromPackageScreen({ route, navigation }: Props) {
  const { userPackageId } = route.params;
  const [slots, setSlots] = useState<ClassSlot[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [scheduling, setScheduling] = useState<string | null>(null);

  useEffect(() => {
    const q = query(collection(db, 'classSlots'), where('status', '==', 'open'), orderBy('date', 'asc'));
    const unsubscribe = onSnapshot(q, (snap) => {
      setSlots(snap.docs.map((d) => ({ id: d.id, ...d.data() } as ClassSlot)));
      setLoading(false);
    });
    return unsubscribe;
  }, []);

  // El "calendario" es simplemente los dias que tienen al menos una clase abierta.
  const availableDates = useMemo(() => Array.from(new Set(slots.map((s) => s.date))), [slots]);

  useEffect(() => {
    if (!selectedDate && availableDates.length > 0) {
      setSelectedDate(availableDates[0]);
    }
  }, [availableDates, selectedDate]);

  const slotsForSelectedDate = useMemo(
    () => slots.filter((s) => s.date === selectedDate),
    [slots, selectedDate]
  );

  const handleSchedule = async (slot: ClassSlot) => {
    setScheduling(slot.id);
    try {
      await scheduleClassFromPackage({ userPackageId, slotId: slot.id });
      Alert.alert('Clase agendada', 'Tu clase quedo reservada usando tu paquete.', [
        { text: 'Listo', onPress: () => navigation.popToTop() },
      ]);
    } catch (err: any) {
      Alert.alert('No se pudo agendar', err?.message ?? 'Intenta nuevamente.');
    } finally {
      setScheduling(null);
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
      <Text style={styles.header}>Elige el dia</Text>
      <FlatList
        horizontal
        showsHorizontalScrollIndicator={false}
        data={availableDates}
        keyExtractor={(item) => item}
        contentContainerStyle={{ paddingHorizontal: 12 }}
        ListEmptyComponent={<Text style={styles.empty}>No hay clases disponibles por ahora.</Text>}
        renderItem={({ item }) => {
          const label = dayLabel(item);
          const isSelected = item === selectedDate;
          return (
            <TouchableOpacity
              style={[styles.dayChip, isSelected && styles.dayChipSelected]}
              onPress={() => setSelectedDate(item)}
            >
              <Text style={[styles.dayWeekday, isSelected && styles.dayTextSelected]}>{label.weekday}</Text>
              <Text style={[styles.dayNumber, isSelected && styles.dayTextSelected]}>{label.day}</Text>
              <Text style={[styles.dayWeekday, isSelected && styles.dayTextSelected]}>{label.month}</Text>
            </TouchableOpacity>
          );
        }}
      />

      <Text style={styles.header}>Elige el horario</Text>
      <FlatList
        data={slotsForSelectedDate}
        keyExtractor={(item) => item.id}
        contentContainerStyle={{ padding: 16, paddingTop: 0 }}
        ListEmptyComponent={<Text style={styles.empty}>No hay horarios para este dia.</Text>}
        renderItem={({ item }) => {
          const full = item.bookedBy.length >= item.capacity;
          return (
            <TouchableOpacity
              style={styles.card}
              disabled={full || scheduling === item.id}
              onPress={() => handleSchedule(item)}
            >
              <Text style={styles.title}>{item.title}</Text>
              <Text style={styles.detail}>
                {item.startTime} - {item.endTime}
              </Text>
              <Text style={styles.detail}>Profesor: {item.coachName} · Nivel: {item.level}</Text>
              <Text style={styles.detail}>Cupos: {item.bookedBy.length}/{item.capacity}</Text>
              <Text style={styles.action}>
                {full ? 'Sin cupos' : scheduling === item.id ? 'Agendando...' : 'Agendar este horario'}
              </Text>
            </TouchableOpacity>
          );
        }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  header: { fontSize: 15, fontWeight: '700', marginHorizontal: 16, marginTop: 16, marginBottom: 8 },
  empty: { textAlign: 'center', color: '#777', marginTop: 20, marginHorizontal: 16 },
  dayChip: {
    width: 56,
    paddingVertical: 10,
    marginRight: 8,
    borderRadius: 10,
    backgroundColor: '#fff',
    alignItems: 'center',
    elevation: 1,
  },
  dayChipSelected: { backgroundColor: '#1b5e20' },
  dayWeekday: { fontSize: 11, color: '#777', textTransform: 'uppercase' },
  dayNumber: { fontSize: 18, fontWeight: '700', color: '#222', marginVertical: 2 },
  dayTextSelected: { color: '#fff' },
  card: { backgroundColor: '#fff', borderRadius: 12, padding: 16, marginBottom: 14, marginTop: 14, elevation: 2 },
  title: { fontSize: 16, fontWeight: '700', marginBottom: 4 },
  detail: { fontSize: 13, color: '#555', marginBottom: 2 },
  action: { fontSize: 14, color: '#1b5e20', fontWeight: '600', marginTop: 8 },
});
