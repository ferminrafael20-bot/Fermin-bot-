import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { useAuth } from '@/context/AuthContext';

export default function HomeScreen() {
  const { profile } = useAuth();

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ padding: 20 }}>
      <Text style={styles.greeting}>Hola, {profile?.name?.split(' ')[0] ?? 'jugador/a'} 🎾</Text>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>Tu suscripcion</Text>
        <Text style={styles.cardBody}>
          {profile?.subscriptionActive
            ? `Plan ${profile.subscriptionPlan} activo. Tienes descuentos en clases y marcas afiliadas.`
            : 'Aun no tienes una suscripcion activa. Suscribete para obtener descuentos.'}
        </Text>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>Que puedes hacer aqui</Text>
        <Text style={styles.cardBody}>• Reservar y pagar clases individuales</Text>
        <Text style={styles.cardBody}>• Mover o cancelar una clase ya reservada</Text>
        <Text style={styles.cardBody}>• Anotarte en grupos de entrenamiento</Text>
        <Text style={styles.cardBody}>• Suscribirte para obtener descuentos</Text>
        <Text style={styles.cardBody}>• Comprar articulos de tenis en la tienda</Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  greeting: { fontSize: 24, fontWeight: '700', marginBottom: 20 },
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    elevation: 2,
  },
  cardTitle: { fontSize: 16, fontWeight: '700', marginBottom: 8, color: '#1b5e20' },
  cardBody: { fontSize: 14, color: '#333', marginBottom: 4 },
});
