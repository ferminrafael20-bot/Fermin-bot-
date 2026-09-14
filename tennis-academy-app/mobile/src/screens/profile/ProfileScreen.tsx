import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Alert } from 'react-native';
import { useAuth } from '@/context/AuthContext';

export default function ProfileScreen() {
  const { profile, firebaseUser, signOut } = useAuth();

  const handleSignOut = () => {
    Alert.alert('Cerrar sesion', 'Seguro que quieres salir?', [
      { text: 'Cancelar', style: 'cancel' },
      { text: 'Cerrar sesion', style: 'destructive', onPress: signOut },
    ]);
  };

  return (
    <View style={styles.container}>
      <View style={styles.card}>
        <Text style={styles.name}>{profile?.name ?? firebaseUser?.email}</Text>
        <Text style={styles.detail}>{profile?.email}</Text>
        {profile?.phone ? <Text style={styles.detail}>{profile.phone}</Text> : null}
        <Text style={styles.detail}>Rol: {profile?.role ?? 'student'}</Text>
      </View>

      <TouchableOpacity style={styles.button} onPress={handleSignOut}>
        <Text style={styles.buttonText}>Cerrar sesion</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20, backgroundColor: '#f5f5f5' },
  card: { backgroundColor: '#fff', borderRadius: 12, padding: 20, marginBottom: 20, elevation: 2 },
  name: { fontSize: 20, fontWeight: '700', marginBottom: 6 },
  detail: { fontSize: 14, color: '#555', marginBottom: 4 },
  button: { backgroundColor: '#b71c1c', borderRadius: 8, padding: 14 },
  buttonText: { color: '#fff', textAlign: 'center', fontWeight: '600' },
});
