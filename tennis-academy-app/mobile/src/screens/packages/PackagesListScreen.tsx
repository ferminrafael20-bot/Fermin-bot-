import React, { useEffect, useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, Alert, ActivityIndicator } from 'react-native';
import { collection, onSnapshot, query, where } from 'firebase/firestore';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { db } from '@/firebase/config';
import { ClassPackage } from '@/types';
import { purchaseClassPackage } from '@/services/api';
import { ClassesStackParamList } from '@/navigation/ClassesNavigator';

type Props = NativeStackScreenProps<ClassesStackParamList, 'Packages'>;

export default function PackagesListScreen({ navigation }: Props) {
  const [packages, setPackages] = useState<ClassPackage[]>([]);
  const [loading, setLoading] = useState(true);
  const [buyingId, setBuyingId] = useState<string | null>(null);

  useEffect(() => {
    const q = query(collection(db, 'classPackages'), where('active', '==', true));
    const unsubscribe = onSnapshot(q, (snap) => {
      setPackages(snap.docs.map((d) => ({ id: d.id, ...d.data() } as ClassPackage)));
      setLoading(false);
    });
    return unsubscribe;
  }, []);

  const handleBuy = async (pkg: ClassPackage) => {
    setBuyingId(pkg.id);
    try {
      const { data } = await purchaseClassPackage({ packageId: pkg.id });
      navigation.navigate('WebpayCheckout', {
        url: data.url,
        token: data.token,
        purpose: 'classPackage',
        purposeId: data.paymentId,
      });
    } catch (err: any) {
      Alert.alert('No se pudo iniciar la compra', err?.message ?? 'Intenta nuevamente.');
    } finally {
      setBuyingId(null);
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
      <TouchableOpacity style={styles.myPackagesButton} onPress={() => navigation.navigate('MyPackages')}>
        <Text style={styles.myPackagesText}>Ver mis paquetes</Text>
      </TouchableOpacity>

      <FlatList
        data={packages}
        keyExtractor={(item) => item.id}
        contentContainerStyle={{ padding: 16 }}
        ListEmptyComponent={<Text style={styles.empty}>No hay paquetes disponibles por ahora.</Text>}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <Text style={styles.title}>{item.name}</Text>
            <Text style={styles.detail}>
              {item.classCount} clases · validas por {item.validityDays} dias
            </Text>
            {item.description ? <Text style={styles.detail}>{item.description}</Text> : null}
            <Text style={styles.price}>${item.price.toLocaleString('es-CL')}</Text>
            <TouchableOpacity
              style={styles.button}
              disabled={buyingId === item.id}
              onPress={() => handleBuy(item)}
            >
              <Text style={styles.buttonText}>
                {buyingId === item.id ? 'Procesando...' : 'Comprar y pagar'}
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
  myPackagesButton: { padding: 14, backgroundColor: '#e8f5e9' },
  myPackagesText: { textAlign: 'center', color: '#1b5e20', fontWeight: '600' },
  empty: { textAlign: 'center', color: '#777', marginTop: 40 },
  card: { backgroundColor: '#fff', borderRadius: 12, padding: 16, marginBottom: 14, elevation: 2 },
  title: { fontSize: 16, fontWeight: '700', marginBottom: 4 },
  detail: { fontSize: 13, color: '#555', marginBottom: 2 },
  price: { fontSize: 16, fontWeight: '700', color: '#1b5e20', marginTop: 8, marginBottom: 8 },
  button: { backgroundColor: '#1b5e20', borderRadius: 8, padding: 10 },
  buttonText: { color: '#fff', textAlign: 'center', fontWeight: '600' },
});
