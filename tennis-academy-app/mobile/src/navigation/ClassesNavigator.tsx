import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import ClassesListScreen from '@/screens/classes/ClassesListScreen';
import MyBookingsScreen from '@/screens/classes/MyBookingsScreen';
import MoveBookingScreen from '@/screens/classes/MoveBookingScreen';
import WebpayCheckoutScreen from '@/screens/payment/WebpayCheckoutScreen';

export type ClassesStackParamList = {
  ClassesList: undefined;
  MyBookings: undefined;
  MoveBooking: { bookingId: string };
  WebpayCheckout: { url: string; token: string; purpose: string; purposeId: string };
};

const Stack = createNativeStackNavigator<ClassesStackParamList>();

export default function ClassesNavigator() {
  return (
    <Stack.Navigator>
      <Stack.Screen name="ClassesList" component={ClassesListScreen} options={{ title: 'Clases disponibles' }} />
      <Stack.Screen name="MyBookings" component={MyBookingsScreen} options={{ title: 'Mis clases' }} />
      <Stack.Screen name="MoveBooking" component={MoveBookingScreen} options={{ title: 'Mover clase' }} />
      <Stack.Screen name="WebpayCheckout" component={WebpayCheckoutScreen} options={{ title: 'Pago con Webpay' }} />
    </Stack.Navigator>
  );
}
