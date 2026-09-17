import React, { useRef, useState } from 'react';
import { View, ActivityIndicator, StyleSheet, Alert } from 'react-native';
import { WebView, WebViewNavigation } from 'react-native-webview';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { confirmWebpayTransaction } from '@/services/api';

type Params = { url: string; token: string; purpose: string; purposeId: string };
type Props = NativeStackScreenProps<{ WebpayCheckout: Params }, 'WebpayCheckout'>;

// La Cloud Function webpayReturn (functions/src/webpay.ts) recibe el POST de vuelta
// de Transbank y redirige a este esquema propio de la app. Un esquema custom no es una
// URL "navegable" real, asi que hay que interceptarlo con onShouldStartLoadWithRequest
// (onNavigationStateChange no siempre dispara para esquemas que el WebView no sabe cargar).
const RETURN_URL_MARKER = 'academiatenis://webpay-return';

export default function WebpayCheckoutScreen({ route, navigation }: Props) {
  const { url, token, purpose, purposeId } = route.params;
  const [confirming, setConfirming] = useState(false);
  const handledRef = useRef(false);

  const handleReturn = async () => {
    if (handledRef.current) return;
    handledRef.current = true;
    setConfirming(true);
    try {
      const { data } = await confirmWebpayTransaction({ token });
      if (data.status === 'AUTHORIZED') {
        Alert.alert('Pago exitoso', 'Tu pago fue confirmado correctamente.', [
          { text: 'Listo', onPress: () => navigation.popToTop() },
        ]);
      } else {
        Alert.alert('Pago rechazado', 'Transbank rechazo el pago. Intenta nuevamente.', [
          { text: 'Ok', onPress: () => navigation.goBack() },
        ]);
      }
    } catch (err: any) {
      Alert.alert('No se pudo confirmar el pago', err?.message ?? 'Contacta a la academia.');
    } finally {
      setConfirming(false);
    }
  };

  const handleShouldStartLoad = (navState: WebViewNavigation) => {
    if (navState.url.startsWith(RETURN_URL_MARKER)) {
      handleReturn();
      return false;
    }
    return true;
  };

  return (
    <View style={styles.container}>
      <WebView
        source={{ uri: `${url}?token_ws=${token}` }}
        onShouldStartLoadWithRequest={handleShouldStartLoad}
        startInLoadingState
        renderLoading={() => (
          <View style={styles.center}>
            <ActivityIndicator size="large" color="#1b5e20" />
          </View>
        )}
      />
      {confirming && (
        <View style={styles.overlay}>
          <ActivityIndicator size="large" color="#fff" />
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  overlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
});
