import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import ClassesListScreen from '@/screens/classes/ClassesListScreen';
import MyBookingsScreen from '@/screens/classes/MyBookingsScreen';
import MoveBookingScreen from '@/screens/classes/MoveBookingScreen';
import PackagesListScreen from '@/screens/packages/PackagesListScreen';
import MyPackagesScreen from '@/screens/packages/MyPackagesScreen';
import ScheduleFromPackageScreen from '@/screens/packages/ScheduleFromPackageScreen';
import WebpayCheckoutScreen from '@/screens/payment/WebpayCheckoutScreen';

export type ClassesStackParamList = {
  ClassesList: undefined;
  MyBookings: undefined;
  MoveBooking: { bookingId: string };
  Packages: undefined;
  MyPackages: undefined;
  ScheduleFromPackage: { userPackageId: string };
  WebpayCheckout: { url: string; token: string; purpose: string; purposeId: string };
};

const Stack = createNativeStackNavigator<ClassesStackParamList>();

export default function ClassesNavigator() {
  return (
    <Stack.Navigator>
      <Stack.Screen name="ClassesList" component={ClassesListScreen} options={{ title: 'Clases disponibles' }} />
      <Stack.Screen name="MyBookings" component={MyBookingsScreen} options={{ title: 'Mis clases' }} />
      <Stack.Screen name="MoveBooking" component={MoveBookingScreen} options={{ title: 'Mover clase' }} />
      <Stack.Screen name="Packages" component={PackagesListScreen} options={{ title: 'Paquetes de clases' }} />
      <Stack.Screen name="MyPackages" component={MyPackagesScreen} options={{ title: 'Mis paquetes' }} />
      <Stack.Screen
        name="ScheduleFromPackage"
        component={ScheduleFromPackageScreen}
        options={{ title: 'Agendar clase del paquete' }}
      />
      <Stack.Screen name="WebpayCheckout" component={WebpayCheckoutScreen} options={{ title: 'Pago con Webpay' }} />
    </Stack.Navigator>
  );
}
