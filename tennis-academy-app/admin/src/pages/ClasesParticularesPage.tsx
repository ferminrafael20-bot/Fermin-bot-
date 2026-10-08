import React, { useEffect, useState } from 'react';
import { addDoc, collection, deleteDoc, doc, onSnapshot, orderBy, query, updateDoc } from 'firebase/firestore';
import { db } from '@/firebase/config';
import { ClassSlot, Level } from '@/types';
import { useCoaches } from '@/hooks/useCoaches';
import Modal from '@/components/Modal';

const EMPTY_FORM = {
  title: '',
  coachId: '',
  date: '',
  startTime: '',
  endTime: '',
  capacity: 1,
  price: 0,
  level: 'principiante' as Level,
};

export default function ClasesParticularesPage() {
  const coaches = useCoaches();
  const [slots, setSlots] = useState<ClassSlot[]>([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState<ClassSlot | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const q = query(collection(db, 'classSlots'), orderBy('date', 'asc'));
    const unsubscribe = onSnapshot(q, (snap) => {
      setSlots(snap.docs.map((d) => ({ id: d.id, ...d.data() } as ClassSlot)));
      setLoading(false);
    });
    return unsubscribe;
  }, []);

  const openCreate = () => {
    setEditing(null);
    setForm({ ...EMPTY_FORM, coachId: coaches[0]?.id ?? '' });
    setShowForm(true);
  };

  const openEdit = (slot: ClassSlot) => {
    setEditing(slot);
    setForm({
      title: slot.title,
      coachId: slot.coachId,
      date: slot.date,
      startTime: slot.startTime,
      endTime: slot.endTime,
      capacity: slot.capacity,
      price: slot.price,
      level: slot.level,
    });
    setShowForm(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    const takenCount = editing ? editing.bookedBy.length + Object.keys(editing.pendingHolds ?? {}).length : 0;
    if (form.capacity < takenCount) {
      alert(`No puedes bajar el cupo por debajo de ${takenCount} (ya hay alumnos reservados).`);
      return;
    }
    const coach = coaches.find((c) => c.id === form.coachId);
    if (!coach) {
      alert('Selecciona un profesor.');
      return;
    }

    setSaving(true);
    try {
      const payload = { ...form, coachName: coach.name };
      if (editing) {
        await updateDoc(doc(db, 'classSlots', editing.id), payload);
      } else {
        await addDoc(collection(db, 'classSlots'), {
          ...payload,
          bookedBy: [],
          pendingHolds: {},
          status: 'open',
        });
      }
      setShowForm(false);
    } finally {
      setSaving(false);
    }
  };

  const handleCancelClass = async (slot: ClassSlot) => {
    if (!confirm(`Cancelar la clase "${slot.title}" del ${slot.date}? Los alumnos ya no podran reservarla.`)) return;
    await updateDoc(doc(db, 'classSlots', slot.id), { status: 'cancelled' });
  };

  const handleDelete = async (slot: ClassSlot) => {
    if (slot.bookedBy.length > 0) {
      alert('No puedes eliminar una clase con alumnos reservados. Cancelala en su lugar.');
      return;
    }
    if (!confirm('Eliminar esta clase?')) return;
    await deleteDoc(doc(db, 'classSlots', slot.id));
  };

  return (
    <div>
      <div className="page-header">
        <h1>Clases particulares</h1>
        <button className="btn" onClick={openCreate} disabled={coaches.length === 0}>+ Nueva clase</button>
      </div>
      {coaches.length === 0 && (
        <p className="empty-state">Primero registra al menos un profesor en la seccion "Profesores".</p>
      )}

      <div className="card" style={{ padding: 0 }}>
        {loading ? (
          <p style={{ padding: 20 }}>Cargando...</p>
        ) : slots.length === 0 ? (
          <p className="empty-state">Aun no hay clases particulares creadas.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Clase</th>
                <th>Fecha / horario</th>
                <th>Profesor</th>
                <th>Cupos</th>
                <th>Precio</th>
                <th>Estado</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {slots.map((slot) => (
                <tr key={slot.id}>
                  <td>{slot.title} <span style={{ color: 'var(--color-text-muted)' }}>({slot.level})</span></td>
                  <td>{slot.date} · {slot.startTime}-{slot.endTime}</td>
                  <td>{slot.coachName}</td>
                  <td>{slot.bookedBy.length}/{slot.capacity}</td>
                  <td>${slot.price.toLocaleString('es-CL')}</td>
                  <td><span className={`badge badge-${slot.status}`}>{slot.status}</span></td>
                  <td style={{ display: 'flex', gap: 8 }}>
                    <button className="btn-secondary btn" onClick={() => openEdit(slot)}>Editar</button>
                    {slot.status !== 'cancelled' && (
                      <button className="btn-secondary btn" onClick={() => handleCancelClass(slot)}>Cancelar</button>
                    )}
                    <button className="btn-danger btn" onClick={() => handleDelete(slot)}>Eliminar</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {showForm && (
        <Modal title={editing ? 'Editar clase' : 'Nueva clase particular'} onClose={() => setShowForm(false)}>
          <form onSubmit={handleSave}>
            <div className="field">
              <label>Titulo</label>
              <input required value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
            </div>
            <div className="field">
              <label>Profesor</label>
              <select required value={form.coachId} onChange={(e) => setForm({ ...form, coachId: e.target.value })}>
                <option value="" disabled>Selecciona un profesor</option>
                {coaches.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>Fecha</label>
              <input type="date" required value={form.date} onChange={(e) => setForm({ ...form, date: e.target.value })} />
            </div>
            <div style={{ display: 'flex', gap: 12 }}>
              <div className="field" style={{ flex: 1 }}>
                <label>Hora inicio</label>
                <input type="time" required value={form.startTime} onChange={(e) => setForm({ ...form, startTime: e.target.value })} />
              </div>
              <div className="field" style={{ flex: 1 }}>
                <label>Hora fin</label>
                <input type="time" required value={form.endTime} onChange={(e) => setForm({ ...form, endTime: e.target.value })} />
              </div>
            </div>
            <div style={{ display: 'flex', gap: 12 }}>
              <div className="field" style={{ flex: 1 }}>
                <label>Cupos</label>
                <input type="number" min={1} required value={form.capacity} onChange={(e) => setForm({ ...form, capacity: Number(e.target.value) })} />
              </div>
              <div className="field" style={{ flex: 1 }}>
                <label>Precio (CLP)</label>
                <input type="number" min={0} required value={form.price} onChange={(e) => setForm({ ...form, price: Number(e.target.value) })} />
              </div>
            </div>
            <div className="field">
              <label>Nivel</label>
              <select value={form.level} onChange={(e) => setForm({ ...form, level: e.target.value as Level })}>
                <option value="principiante">Principiante</option>
                <option value="intermedio">Intermedio</option>
                <option value="avanzado">Avanzado</option>
              </select>
            </div>
            <button className="btn" type="submit" disabled={saving} style={{ width: '100%', marginTop: 8 }}>
              {saving ? 'Guardando...' : 'Guardar'}
            </button>
          </form>
        </Modal>
      )}
    </div>
  );
}
