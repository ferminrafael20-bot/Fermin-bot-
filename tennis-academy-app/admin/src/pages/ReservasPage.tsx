import React, { useEffect, useState } from 'react';
import { collection, doc, getDoc, onSnapshot, orderBy, query } from 'firebase/firestore';
import { db } from '@/firebase/config';
import { Booking, BookingStatus, ClassSlot } from '@/types';
import { adminCancelBooking } from '@/services/api';

interface Row extends Booking {
  slot?: ClassSlot;
  userName?: string;
}

const STATUS_LABEL: Record<BookingStatus, string> = {
  pending_payment: 'Pago pendiente',
  confirmed: 'Confirmada',
  moved: 'Movida',
  cancelled: 'Cancelada',
};

const STATUS_BADGE: Record<BookingStatus, string> = {
  pending_payment: 'badge-pending',
  confirmed: 'badge-confirmed',
  moved: 'badge-confirmed',
  cancelled: 'badge-cancelled',
};

export default function ReservasPage() {
  const [rows, setRows] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<BookingStatus | 'all'>('all');
  const [cancellingId, setCancellingId] = useState<string | null>(null);

  useEffect(() => {
    const q = query(collection(db, 'bookings'), orderBy('createdAt', 'desc'));
    const unsubscribe = onSnapshot(q, async (snap) => {
      const bookings = snap.docs.map((d) => ({ id: d.id, ...d.data() } as Booking));
      const enriched = await Promise.all(
        bookings.map(async (booking) => {
          const [slotSnap, userSnap] = await Promise.all([
            getDoc(doc(db, 'classSlots', booking.slotId)),
            getDoc(doc(db, 'users', booking.userId)),
          ]);
          return {
            ...booking,
            slot: slotSnap.exists() ? (slotSnap.data() as ClassSlot) : undefined,
            userName: userSnap.exists() ? (userSnap.data() as any).name : booking.userId,
          } as Row;
        })
      );
      setRows(enriched);
      setLoading(false);
    });
    return unsubscribe;
  }, []);

  const handleCancel = async (row: Row) => {
    if (!confirm(`Cancelar la reserva de ${row.userName}?`)) return;
    setCancellingId(row.id);
    try {
      await adminCancelBooking({ bookingId: row.id });
    } catch (err: any) {
      alert(err?.message ?? 'No se pudo cancelar la reserva.');
    } finally {
      setCancellingId(null);
    }
  };

  const visibleRows = filter === 'all' ? rows : rows.filter((r) => r.status === filter);

  return (
    <div>
      <div className="page-header">
        <h1>Reservas</h1>
        <select value={filter} onChange={(e) => setFilter(e.target.value as BookingStatus | 'all')}>
          <option value="all">Todas</option>
          <option value="pending_payment">Pago pendiente</option>
          <option value="confirmed">Confirmadas</option>
          <option value="moved">Movidas</option>
          <option value="cancelled">Canceladas</option>
        </select>
      </div>

      <div className="card" style={{ padding: 0 }}>
        {loading ? (
          <p style={{ padding: 20 }}>Cargando...</p>
        ) : visibleRows.length === 0 ? (
          <p className="empty-state">No hay reservas para este filtro.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Alumno</th>
                <th>Clase</th>
                <th>Fecha</th>
                <th>Estado</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {visibleRows.map((row) => (
                <tr key={row.id}>
                  <td>{row.userName}</td>
                  <td>{row.slot?.title ?? 'Clase eliminada'}</td>
                  <td>{row.slot ? `${row.slot.date} · ${row.slot.startTime}-${row.slot.endTime}` : '-'}</td>
                  <td>
                    <span className={`badge ${STATUS_BADGE[row.status]}`}>{STATUS_LABEL[row.status]}</span>
                  </td>
                  <td>
                    {row.status !== 'cancelled' && (
                      <button
                        className="btn-danger btn"
                        disabled={cancellingId === row.id}
                        onClick={() => handleCancel(row)}
                      >
                        {cancellingId === row.id ? 'Cancelando...' : 'Cancelar'}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
