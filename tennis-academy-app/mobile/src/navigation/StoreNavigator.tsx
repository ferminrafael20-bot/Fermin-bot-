import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import StoreListScreen from '@/screens/store/StoreListScreen';
import ProductDetailScreen from '@/screens/store/ProductDetailScreen';
import WebpayCheckoutScreen from '@/screens/payment/WebpayCheckoutScreen';

export type StoreStackParamList = {
  StoreList: undefined;
  ProductDetail: { productId: string };
  WebpayCheckout: { url: string; token: string; purpose: string; purposeId: string };
};

const Stack = createNativeStackNavigator<StoreStackParamList>();

export default function StoreNavigator() {
  return (
    <Stack.Navigator>
      <Stack.Screen name="StoreList" component={StoreListScreen} options={{ title: 'Tienda' }} />
      <Stack.Screen name="ProductDetail" component={ProductDetailScreen} options={{ title: 'Producto' }} />
      <Stack.Screen name="WebpayCheckout" component={WebpayCheckoutScreen} options={{ title: 'Pago con Webpay' }} />
    </Stack.Navigator>
  );
}
