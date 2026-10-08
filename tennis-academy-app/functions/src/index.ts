import { setGlobalOptions } from 'firebase-functions/v2';

// Mismo continente que la base de datos Firestore (southamerica-east1, Sao Paulo) para
// no agregar latencia extra entre las Functions y Firestore/Webpay/los usuarios en Chile.
setGlobalOptions({ region: 'southamerica-east1' });

export { bookClass, moveBooking, cancelBooking, adminCancelBooking, releaseExpiredHolds } from './bookings';
export { joinTrainingGroup, leaveTrainingGroup } from './groups';
export { startSubscription, cancelSubscription } from './subscriptions';
export { createWebpayTransaction, confirmWebpayTransaction, webpayReturn } from './webpay';
export { refreshStoreProducts, refreshStoreProductsScheduled } from './scraper';
