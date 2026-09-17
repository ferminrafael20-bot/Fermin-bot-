import { HttpsError } from 'firebase-functions/v2/https';
import {
  WebpayPlus,
  Options,
  Environment,
  IntegrationApiKeys,
  IntegrationCommerceCodes,
} from 'transbank-sdk';

export function getWebpayTransaction(): InstanceType<typeof WebpayPlus.Transaction> {
  if (process.env.WEBPAY_ENV === 'production') {
    const commerceCode = process.env.WEBPAY_COMMERCE_CODE;
    const apiKey = process.env.WEBPAY_API_KEY;
    if (!commerceCode || !apiKey) {
      throw new HttpsError('failed-precondition', 'Webpay no esta configurado para produccion.');
    }
    return new WebpayPlus.Transaction(new Options(commerceCode, apiKey, Environment.Production));
  }
  // Credenciales de integracion (pruebas) publicadas por Transbank; no son secretas.
  return new WebpayPlus.Transaction(
    new Options(IntegrationCommerceCodes.WEBPAY_PLUS, IntegrationApiKeys.WEBPAY, Environment.Integration)
  );
}

export function getWebpayReturnUrl(): string {
  const url = process.env.WEBPAY_RETURN_URL;
  if (!url) {
    throw new HttpsError(
      'failed-precondition',
      'Falta configurar WEBPAY_RETURN_URL (la URL publica de la funcion webpayReturn).'
    );
  }
  return url;
}
