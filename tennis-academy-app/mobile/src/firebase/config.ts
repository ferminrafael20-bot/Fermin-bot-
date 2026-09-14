import { initializeApp, getApps, getApp } from 'firebase/app';
// getReactNativePersistence solo esta tipado en la build RN de @firebase/auth; el
// bundler de Expo/Metro la resuelve igual en tiempo de ejecucion, pero "tsc" (usado por
// npm run typecheck) resuelve el paquete web y no encuentra el tipo. Ver mobile/README.
// @ts-ignore
import { initializeAuth, getReactNativePersistence, getAuth } from 'firebase/auth';
import { getFirestore } from 'firebase/firestore';
import { getFunctions } from 'firebase/functions';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Todas estas claves son publicas (config "web" de Firebase), no secretas.
// Se completan en mobile/.env (ver .env.example) y Expo las expone via process.env
// gracias al prefijo EXPO_PUBLIC_.
const firebaseConfig = {
  apiKey: process.env.EXPO_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.EXPO_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.EXPO_PUBLIC_FIREBASE_PROJECT_ID,
  storageBucket: process.env.EXPO_PUBLIC_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.EXPO_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.EXPO_PUBLIC_FIREBASE_APP_ID,
};

// Se calcula antes de inicializar la app: initializeApp() de abajo agrega una entrada a
// getApps(), asi que si se revisara despues siempre parecería que "ya existia".
const wasAlreadyInitialized = getApps().length > 0;

export const firebaseApp = wasAlreadyInitialized ? getApp() : initializeApp(firebaseConfig);

// initializeAuth con persistencia solo puede llamarse una vez por instancia de la app.
export const auth = wasAlreadyInitialized
  ? getAuth(firebaseApp)
  : initializeAuth(firebaseApp, {
      persistence: getReactNativePersistence(AsyncStorage),
    });

export const db = getFirestore(firebaseApp);

export const functions = getFunctions(
  firebaseApp,
  process.env.EXPO_PUBLIC_FUNCTIONS_REGION || 'us-central1'
);
