import React, { useEffect, useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, Alert, ActivityIndicator } from 'react-native';
import { collection, onSnapshot } from 'firebase/firestore';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { db } from '@/firebase/config';
import { useAuth } from '@/context/AuthContext';
import { AffiliatedBrand, SubscriptionPlan } from '@/types';
import { startSubscription, cancelSubscription } from '@/services/api';
import { SubscriptionStackParamList } from '@/navigation/SubscriptionNavigator';

type Props = NativeStackScreenProps<SubscriptionStackParamList, 'Subscription'>;

const PLANS: { id: SubscriptionPlan; name: string; price: number; discount: number }[] = [
  { id: 'basic', name: 'Basico', price: 9990, discount: 5 },
  { id: 'plus', name: 'Plus', price: 19990, discount: 12 },
  { id: 'pro', name: 'Pro', price: 29990, discount: 20 },
];

export default function SubscriptionScreen({ navigation }: Props) {
  const { profile } = useAuth();
  const [brands, setBrands] = useState<AffiliatedBrand[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyPlan, setBusyPlan] = useState<SubscriptionPlan | null>(null);

  useEffect(() => {
    const unsubscribe = onSnapshot(collection(db, 'affiliatedBrands'), (snap) => {
      setBrands(snap.docs.map((d) => ({ id: d.id, ...d.data() } as AffiliatedBrand)));
      setLoading(false);
    });
    return unsubscribe;
  }, []);

  const handleSubscribe = async (plan: SubscriptionPlan) => {
    setBusyPlan(plan);
    try {
      const { data } = await startSubscription({ plan });
      navigation.navigate('WebpayCheckout', {
        url: data.url,
        token: data.token,
        purpose: 'subscription',
        purposeId: data.paymentId,
      });
    } catch (err: any) {
      Alert.alert('No se pudo suscribir', err?.message ?? 'Intenta nuevamente.');
    } finally {
      setBusyPlan(null);
    }
  };

  const handleCancel = () => {
    Alert.alert('Cancelar suscripcion', 'Perderas tus descuentos activos. Continuar?', [
      { text: 'No', style: 'cancel' },
      {
        text: 'Si, cancelar',
        style: 'destructive',
        onPress: async () => {
          try {
            await cancelSubscription({});
          } catch (err: any) {
            Alert.alert('No se pudo cancelar', err?.message ?? 'Intenta nuevamente.');
          }
        },
      },
    ]);
  };

  return (
    <FlatList
      style={styles.container}
      contentContainerStyle={{ padding: 16 }}
      data={brands}
      keyExtractor={(item) => item.id}
      ListHeaderComponent={
        <View>
          <Text style={styles.sectionTitle}>Planes de suscripcion</Text>
          {PLANS.map((plan) => (
            <View key={plan.id} style={styles.card}>
              <Text style={styles.title}>{plan.name}</Text>
              <Text style={styles.detail}>{plan.discount}% de descuento en clases y marcas afiliadas</Text>
              <Text style={styles.price}>${plan.price.toLocaleString('es-CL')} / mes</Text>
              {profile?.subscriptionActive && profile.subscriptionPlan === plan.id ? (
                <TouchableOpacity style={styles.dangerButton} onPress={handleCancel}>
                  <Text style={styles.buttonText}>Cancelar mi plan</Text>
                </TouchableOpacity>
              ) : (
                <TouchableOpacity
                  style={styles.button}
                  disabled={busyPlan === plan.id}
                  onPress={() => handleSubscribe(plan.id)}
                >
                  <Text style={styles.buttonText}>{busyPlan === plan.id ? 'Procesando...' : 'Suscribirme'}</Text>
                </TouchableOpacity>
              )}
            </View>
          ))}
          <Text style={styles.sectionTitle}>Marcas afiliadas</Text>
          {loading && <ActivityIndicator color="#1b5e20" />}
        </View>
      }
      ListEmptyComponent={
        !loading ? <Text style={styles.empty}>Aun no hay marcas afiliadas cargadas.</Text> : null
      }
      renderItem={({ item }) => (
        <View style={styles.card}>
          <Text style={styles.title}>{item.name}</Text>
          {item.description ? <Text style={styles.detail}>{item.description}</Text> : null}
          <Text style={styles.detail}>Codigo de descuento: {item.code}</Text>
          <Text style={styles.price}>{item.discountPercent}% de descuento</Text>
        </View>
      )}
    />
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  sectionTitle: { fontSize: 16, fontWeight: '700', marginTop: 8, marginBottom: 12 },
  empty: { textAlign: 'center', color: '#777', marginTop: 20 },
  card: { backgroundColor: '#fff', borderRadius: 12, padding: 16, marginBottom: 14, elevation: 2 },
  title: { fontSize: 16, fontWeight: '700', marginBottom: 4 },
  detail: { fontSize: 13, color: '#555', marginBottom: 2 },
  price: { fontSize: 16, fontWeight: '700', color: '#1b5e20', marginTop: 8, marginBottom: 8 },
  button: { backgroundColor: '#1b5e20', borderRadius: 8, padding: 10 },
  dangerButton: { backgroundColor: '#b71c1c', borderRadius: 8, padding: 10 },
  buttonText: { color: '#fff', textAlign: 'center', fontWeight: '600' },
});
