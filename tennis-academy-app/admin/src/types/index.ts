export type UserRole = 'student' | 'coach' | 'admin';

export interface AppUser {
  uid: string;
  name: string;
  email: string;
  role: UserRole;
}

export type CoachSpecialty = 'individual' | 'grupal' | 'ambas';

export interface Coach {
  id: string;
  name: string;
  photoUrl?: string;
  phone?: string;
  email?: string;
  specialty: CoachSpecialty;
  active: boolean;
}

export type Level = 'principiante' | 'intermedio' | 'avanzado';

export interface ClassSlot {
  id: string;
  title: string;
  coachId: string;
  coachName: string;
  date: string;
  startTime: string;
  endTime: string;
  capacity: number;
  bookedBy: string[];
  pendingHolds?: Record<string, { bookingId: string; expiresAt: number }>;
  price: number;
  level: Level;
  status: 'open' | 'full' | 'cancelled';
}

export interface TrainingGroup {
  id: string;
  name: string;
  level: Level;
  coachId: string;
  coachName: string;
  schedule: string;
  capacity: number;
  memberIds: string[];
  pendingMemberIds?: string[];
  monthlyPrice: number;
}

export type BookingStatus = 'pending_payment' | 'confirmed' | 'moved' | 'cancelled';

export interface Booking {
  id: string;
  userId: string;
  slotId: string;
  status: BookingStatus;
  paymentId?: string;
  createdAt: any;
}

export interface AffiliatedBrand {
  id: string;
  name: string;
  logoUrl?: string;
  discountPercent: number;
  code: string;
  description?: string;
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
