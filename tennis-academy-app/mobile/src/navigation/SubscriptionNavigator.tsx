import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import SubscriptionScreen from '@/screens/subscription/SubscriptionScreen';
import WebpayCheckoutScreen from '@/screens/payment/WebpayCheckoutScreen';

export type SubscriptionStackParamList = {
  Subscription: undefined;
  WebpayCheckout: { url: string; token: string; purpose: string; purposeId: string };
};

const Stack = createNativeStackNavigator<SubscriptionStackParamList>();

export default function SubscriptionNavigator() {
  return (
    <Stack.Navigator>
      <Stack.Screen name="Subscription" component={SubscriptionScreen} options={{ title: 'Suscripcion y descuentos' }} />
      <Stack.Screen name="WebpayCheckout" component={WebpayCheckoutScreen} options={{ title: 'Pago con Webpay' }} />
    </Stack.Navigator>
  );
}
