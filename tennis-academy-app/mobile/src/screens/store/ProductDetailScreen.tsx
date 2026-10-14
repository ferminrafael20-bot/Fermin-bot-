import React, { useEffect, useState } from 'react';
import { View, Text, Image, ScrollView, TouchableOpacity, StyleSheet, Alert, ActivityIndicator } from 'react-native';
import { doc, getDoc } from 'firebase/firestore';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { db } from '@/firebase/config';
import { Product } from '@/types';
import { createWebpayTransaction } from '@/services/api';
import { StoreStackParamList } from '@/navigation/StoreNavigator';

type Props = NativeStackScreenProps<StoreStackParamList, 'ProductDetail'>;

export default function ProductDetailScreen({ route, navigation }: Props) {
  const { productId } = route.params;
  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(true);
  const [buying, setBuying] = useState(false);

  useEffect(() => {
    (async () => {
      const snap = await getDoc(doc(db, 'products', productId));
      if (snap.exists()) setProduct({ id: snap.id, ...snap.data() } as Product);
      setLoading(false);
    })();
  }, [productId]);

  const handleBuy = async () => {
    if (!product) return;
    setBuying(true);
    try {
      const { data } = await createWebpayTransaction({
        purpose: 'store',
        purposeId: product.id,
        amount: product.price,
      });
      navigation.navigate('WebpayCheckout', {
        url: data.url,
        token: data.token,
        purpose: 'store',
        purposeId: product.id,
      });
    } catch (err: any) {
      Alert.alert('No se pudo iniciar el pago', err?.message ?? 'Intenta nuevamente.');
    } finally {
      setBuying(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#1b5e20" />
      </View>
    );
  }

  if (!product) {
    return (
      <View style={styles.center}>
        <Text>Producto no encontrado.</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <Image source={{ uri: product.imageUrl }} style={styles.image} resizeMode="cover" />
      <View style={{ padding: 16 }}>
        <Text style={styles.title}>{product.title}</Text>
        <Text style={styles.price}>
          {product.currency} {product.price.toLocaleString('es-CL')}
        </Text>
        <Text style={styles.detail}>Categoria: {product.category}</Text>
        <Text style={styles.sourceNote}>Producto obtenido desde Mercado Libre. El stock y precio pueden variar.</Text>

        <TouchableOpacity style={styles.button} onPress={handleBuy} disabled={buying}>
          <Text style={styles.buttonText}>{buying ? 'Procesando...' : 'Comprar con Webpay'}</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  image: { width: '100%', height: 260, backgroundColor: '#eee' },
  title: { fontSize: 20, fontWeight: '700', marginBottom: 8 },
  price: { fontSize: 22, fontWeight: '700', color: '#1b5e20', marginBottom: 12 },
  detail: { fontSize: 14, color: '#555', marginBottom: 4 },
  sourceNote: { fontSize: 12, color: '#999', marginTop: 8, marginBottom: 20 },
  button: { backgroundColor: '#1b5e20', borderRadius: 8, padding: 14 },
  buttonText: { color: '#fff', textAlign: 'center', fontWeight: '600', fontSize: 16 },
});
