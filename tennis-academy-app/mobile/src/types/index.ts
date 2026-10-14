export type UserRole = 'student' | 'coach' | 'admin';

export interface AppUser {
  uid: string;
  name: string;
  email: string;
  phone?: string;
  role: UserRole;
  subscriptionActive: boolean;
  subscriptionPlan?: SubscriptionPlan;
  createdAt: number;
}

export type SubscriptionPlan = 'basic' | 'plus' | 'pro';

export interface ClassSlot {
  id: string;
  title: string;
  coachId: string;
  coachName: string;
  date: string; // ISO date, e.g. 2026-09-20
  startTime: string; // HH:mm
  endTime: string; // HH:mm
  capacity: number;
  bookedBy: string[];
  price: number;
  level: 'principiante' | 'intermedio' | 'avanzado';
  status: 'open' | 'full' | 'cancelled';
}

export type BookingStatus = 'pending_payment' | 'confirmed' | 'moved' | 'cancelled';

export interface Booking {
  id: string;
  userId: string;
  slotId: string;
  status: BookingStatus;
  paymentId?: string;
  packageId?: string; // si se agendo usando un credito de un paquete de clases
  createdAt: number;
}

export interface TrainingGroup {
  id: string;
  name: string;
  level: 'principiante' | 'intermedio' | 'avanzado';
  coachId: string;
  coachName: string;
  schedule: string; // e.g. "Lun y Mie 18:00-19:30"
  capacity: number;
  memberIds: string[];
  monthlyPrice: number;
}

export interface AffiliatedBrand {
  id: string;
  name: string;
  logoUrl?: string;
  discountPercent: number;
  code: string;
  description?: string;
}

export interface SubscriptionInfo {
  id: string;
  userId: string;
  plan: SubscriptionPlan;
  status: 'active' | 'cancelled' | 'expired';
  discountPercent: number;
  startDate: number;
  renewalDate: number;
}

export interface Product {
  id: string;
  title: string;
  price: number;
  currency: string;
  imageUrl: string;
  mlUrl: string;
  mlId: string;
  category: string;
  lastScrapedAt: number;
}

export type PaymentPurpose = 'class' | 'subscription' | 'group' | 'store' | 'classPackage';

export interface WebpayTransactionResponse {
  token: string;
  url: string;
  paymentId: string;
}

// --- Paquetes de clases (se compran una vez y se van agendando clase por clase) ---
export interface ClassPackage {
  id: string;
  name: string;
  classCount: number;
  price: number;
  validityDays: number;
  description?: string;
  active: boolean;
}

export type UserPackageStatus = 'active' | 'completed' | 'expired';

export interface UserPackage {
  id: string;
  userId: string;
  packageId: string;
  packageName: string;
  totalClasses: number;
  usedClasses: number;
  remainingClasses: number;
  purchasedAt: number;
  expiresAt: number;
  status: UserPackageStatus;
  paymentId: string;
}
