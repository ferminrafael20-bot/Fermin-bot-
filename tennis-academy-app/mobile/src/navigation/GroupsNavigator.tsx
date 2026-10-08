import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import GroupsListScreen from '@/screens/groups/GroupsListScreen';
import WebpayCheckoutScreen from '@/screens/payment/WebpayCheckoutScreen';

export type GroupsStackParamList = {
  GroupsList: undefined;
  WebpayCheckout: { url: string; token: string; purpose: string; purposeId: string };
};

const Stack = createNativeStackNavigator<GroupsStackParamList>();

export default function GroupsNavigator() {
  return (
    <Stack.Navigator>
      <Stack.Screen name="GroupsList" component={GroupsListScreen} options={{ title: 'Grupos de entrenamiento' }} />
      <Stack.Screen name="WebpayCheckout" component={WebpayCheckoutScreen} options={{ title: 'Pago con Webpay' }} />
    </Stack.Navigator>
  );
}
