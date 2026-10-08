import React, { useEffect, useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, Alert, ActivityIndicator } from 'react-native';
import { collection, onSnapshot } from 'firebase/firestore';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { db } from '@/firebase/config';
import { useAuth } from '@/context/AuthContext';
import { TrainingGroup } from '@/types';
import { joinTrainingGroup, leaveTrainingGroup, createWebpayTransaction } from '@/services/api';
import { GroupsStackParamList } from '@/navigation/GroupsNavigator';

type Props = NativeStackScreenProps<GroupsStackParamList, 'GroupsList'>;

export default function GroupsListScreen({ navigation }: Props) {
  const { firebaseUser } = useAuth();
  const [groups, setGroups] = useState<TrainingGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<string | null>(null);

  useEffect(() => {
    const unsubscribe = onSnapshot(collection(db, 'trainingGroups'), (snap) => {
      setGroups(snap.docs.map((d) => ({ id: d.id, ...d.data() } as TrainingGroup)));
      setLoading(false);
    });
    return unsubscribe;
  }, []);

  const isMember = (group: TrainingGroup) => !!firebaseUser && group.memberIds.includes(firebaseUser.uid);

  const handleJoin = async (group: TrainingGroup) => {
    setBusyId(group.id);
    try {
      await joinTrainingGroup({ groupId: group.id });
      const payment = await createWebpayTransaction({
        purpose: 'group',
        purposeId: group.id,
        amount: group.monthlyPrice,
      });
      navigation.navigate('WebpayCheckout', {
        url: payment.data.url,
        token: payment.data.token,
        purpose: 'group',
        purposeId: group.id,
      });
    } catch (err: any) {
      Alert.alert('No se pudo anotar', err?.message ?? 'Intenta nuevamente.');
    } finally {
      setBusyId(null);
    }
  };

  const handleLeave = (group: TrainingGroup) => {
    Alert.alert('Salir del grupo', `Seguro que quieres salir de "${group.name}"?`, [
      { text: 'Cancelar', style: 'cancel' },
      {
        text: 'Salir',
        style: 'destructive',
        onPress: async () => {
          setBusyId(group.id);
          try {
            await leaveTrainingGroup({ groupId: group.id });
          } catch (err: any) {
            Alert.alert('No se pudo salir del grupo', err?.message ?? 'Intenta nuevamente.');
          } finally {
            setBusyId(null);
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
      data={groups}
      keyExtractor={(item) => item.id}
      ListEmptyComponent={<Text style={styles.empty}>Aun no hay grupos de entrenamiento creados.</Text>}
      renderItem={({ item }) => (
        <View style={styles.card}>
          <Text style={styles.title}>{item.name}</Text>
          <Text style={styles.detail}>Nivel: {item.level} · Profesor: {item.coachName}</Text>
          <Text style={styles.detail}>{item.schedule}</Text>
          <Text style={styles.detail}>Cupos: {item.memberIds.length}/{item.capacity}</Text>
          <Text style={styles.price}>${item.monthlyPrice.toLocaleString('es-CL')} / mes</Text>
          {isMember(item) ? (
            <TouchableOpacity style={styles.dangerButton} disabled={busyId === item.id} onPress={() => handleLeave(item)}>
              <Text style={styles.buttonText}>{busyId === item.id ? 'Procesando...' : 'Salir del grupo'}</Text>
            </TouchableOpacity>
          ) : (
            <TouchableOpacity
              style={styles.button}
              disabled={busyId === item.id || item.memberIds.length >= item.capacity}
              onPress={() => handleJoin(item)}
            >
              <Text style={styles.buttonText}>
                {item.memberIds.length >= item.capacity
                  ? 'Sin cupos'
                  : busyId === item.id
                  ? 'Procesando...'
                  : 'Anotarme y pagar'}
              </Text>
            </TouchableOpacity>
          )}
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
  detail: { fontSize: 13, color: '#555', marginBottom: 2 },
  price: { fontSize: 16, fontWeight: '700', color: '#1b5e20', marginTop: 8, marginBottom: 8 },
  button: { backgroundColor: '#1b5e20', borderRadius: 8, padding: 10 },
  dangerButton: { backgroundColor: '#b71c1c', borderRadius: 8, padding: 10 },
  buttonText: { color: '#fff', textAlign: 'center', fontWeight: '600' },
});
