import React, { useEffect, useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, Image, StyleSheet, ActivityIndicator } from 'react-native';
import { collection, onSnapshot, orderBy, query } from 'firebase/firestore';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { db } from '@/firebase/config';
import { Product } from '@/types';
import { StoreStackParamList } from '@/navigation/StoreNavigator';

type Props = NativeStackScreenProps<StoreStackParamList, 'StoreList'>;

export default function StoreListScreen({ navigation }: Props) {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const q = query(collection(db, 'products'), orderBy('lastScrapedAt', 'desc'));
    const unsubscribe = onSnapshot(q, (snap) => {
      setProducts(snap.docs.map((d) => ({ id: d.id, ...d.data() } as Product)));
      setLoading(false);
    });
    return unsubscribe;
  }, []);

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
      contentContainerStyle={{ padding: 12 }}
      data={products}
      numColumns={2}
      keyExtractor={(item) => item.id}
      ListEmptyComponent={
        <Text style={styles.empty}>
          Todavia no hay productos cargados. Un administrador debe ejecutar la actualizacion del catalogo.
        </Text>
      }
      renderItem={({ item }) => (
        <TouchableOpacity
          style={styles.card}
          onPress={() => navigation.navigate('ProductDetail', { productId: item.id })}
        >
          <Image source={{ uri: item.imageUrl }} style={styles.image} resizeMode="cover" />
          <Text style={styles.title} numberOfLines={2}>{item.title}</Text>
          <Text style={styles.price}>
            {item.currency} {item.price.toLocaleString('es-CL')}
          </Text>
        </TouchableOpacity>
      )}
    />
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  empty: { textAlign: 'center', color: '#777', marginTop: 40, paddingHorizontal: 20 },
  card: {
    flex: 1,
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 10,
    margin: 6,
    elevation: 2,
  },
  image: { width: '100%', height: 120, borderRadius: 8, marginBottom: 8, backgroundColor: '#eee' },
  title: { fontSize: 13, fontWeight: '600', marginBottom: 4 },
  price: { fontSize: 14, fontWeight: '700', color: '#1b5e20' },
});
