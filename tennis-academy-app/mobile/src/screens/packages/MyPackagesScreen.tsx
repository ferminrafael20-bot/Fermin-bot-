import React, { useEffect, useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, ActivityIndicator } from 'react-native';
import { collection, onSnapshot, query, where } from 'firebase/firestore';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { db } from '@/firebase/config';
import { useAuth } from '@/context/AuthContext';
import { UserPackage } from '@/types';
import { ClassesStackParamList } from '@/navigation/ClassesNavigator';

type Props = NativeStackScreenProps<ClassesStackParamList, 'MyPackages'>;

export default function MyPackagesScreen({ navigation }: Props) {
  const { firebaseUser } = useAuth();
  const [packages, setPackages] = useState<UserPackage[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!firebaseUser) return;
    const q = query(collection(db, 'userPackages'), where('userId', '==', firebaseUser.uid));
    const unsubscribe = onSnapshot(q, (snap) => {
      const items = snap.docs.map((d) => ({ id: d.id, ...d.data() } as UserPackage));
      items.sort((a, b) => b.purchasedAt - a.purchasedAt);
      setPackages(items);
      setLoading(false);
    });
    return unsubscribe;
  }, [firebaseUser]);

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
      data={packages}
      keyExtractor={(item) => item.id}
      ListEmptyComponent={<Text style={styles.empty}>Todavia no compraste ningun paquete de clases.</Text>}
      renderItem={({ item }) => {
        const expired = item.expiresAt < Date.now();
        const canSchedule = item.status === 'active' && item.remainingClasses > 0 && !expired;
        return (
          <View style={styles.card}>
            <Text style={styles.title}>{item.packageName}</Text>
            <Text style={styles.detail}>
              {item.remainingClasses} de {item.totalClasses} clases disponibles
            </Text>
            <Text style={styles.detail}>
              Vence el {new Date(item.expiresAt).toLocaleDateString('es-CL')}
            </Text>
            <Text style={[styles.status, expired && styles.statusExpired]}>
              {expired ? 'Vencido' : item.status === 'completed' ? 'Usado por completo' : 'Activo'}
            </Text>
            {canSchedule && (
              <TouchableOpacity
                style={styles.button}
                onPress={() => navigation.navigate('ScheduleFromPackage', { userPackageId: item.id })}
              >
                <Text style={styles.buttonText}>Agendar clase</Text>
              </TouchableOpacity>
            )}
          </View>
        );
      }}
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
  status: { fontSize: 13, fontWeight: '700', color: '#1b5e20', marginTop: 6, marginBottom: 8 },
  statusExpired: { color: '#b71c1c' },
  button: { backgroundColor: '#1b5e20', borderRadius: 8, padding: 10 },
  buttonText: { color: '#fff', textAlign: 'center', fontWeight: '600' },
});
