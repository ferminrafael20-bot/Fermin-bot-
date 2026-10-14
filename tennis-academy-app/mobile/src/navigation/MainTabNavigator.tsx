import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import HomeScreen from '@/screens/HomeScreen';
import ClassesNavigator from './ClassesNavigator';
import GroupsNavigator from './GroupsNavigator';
import SubscriptionNavigator from './SubscriptionNavigator';
import StoreNavigator from './StoreNavigator';
import ProfileScreen from '@/screens/profile/ProfileScreen';

export type MainTabParamList = {
  Home: undefined;
  Classes: undefined;
  Groups: undefined;
  Subscription: undefined;
  Store: undefined;
  Profile: undefined;
};

const Tab = createBottomTabNavigator<MainTabParamList>();

export default function MainTabNavigator() {
  return (
    <Tab.Navigator screenOptions={{ headerShown: false }}>
      <Tab.Screen name="Home" component={HomeScreen} options={{ title: 'Inicio' }} />
      <Tab.Screen name="Classes" component={ClassesNavigator} options={{ title: 'Clases' }} />
      <Tab.Screen name="Groups" component={GroupsNavigator} options={{ title: 'Grupos' }} />
      <Tab.Screen name="Subscription" component={SubscriptionNavigator} options={{ title: 'Suscripcion' }} />
      <Tab.Screen name="Store" component={StoreNavigator} options={{ title: 'Tienda' }} />
      <Tab.Screen name="Profile" component={ProfileScreen} options={{ title: 'Perfil' }} />
    </Tab.Navigator>
  );
}
