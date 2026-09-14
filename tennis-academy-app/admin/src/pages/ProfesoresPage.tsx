import React, { useEffect, useState } from 'react';
import { addDoc, collection, deleteDoc, doc, onSnapshot, updateDoc } from 'firebase/firestore';
import { db } from '@/firebase/config';
import { Coach, CoachSpecialty } from '@/types';
import Modal from '@/components/Modal';

const SPECIALTY_LABEL: Record<CoachSpecialty, string> = {
  individual: 'Clases particulares',
  grupal: 'Clases grupales',
  ambas: 'Particulares y grupales',
};

const EMPTY_FORM = { name: '', phone: '', email: '', photoUrl: '', specialty: 'ambas' as CoachSpecialty };

export default function ProfesoresPage() {
  const [coaches, setCoaches] = useState<Coach[]>([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState<Coach | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const unsubscribe = onSnapshot(collection(db, 'coaches'), (snap) => {
      setCoaches(snap.docs.map((d) => ({ id: d.id, ...d.data() } as Coach)));
      setLoading(false);
    });
    return unsubscribe;
  }, []);

  const openCreate = () => {
    setEditing(null);
    setForm(EMPTY_FORM);
    setShowForm(true);
  };

  const openEdit = (coach: Coach) => {
    setEditing(coach);
    setForm({
      name: coach.name,
      phone: coach.phone ?? '',
      email: coach.email ?? '',
      photoUrl: coach.photoUrl ?? '',
      specialty: coach.specialty,
    });
    setShowForm(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      if (editing) {
        await updateDoc(doc(db, 'coaches', editing.id), { ...form });
      } else {
        await addDoc(collection(db, 'coaches'), { ...form, active: true });
      }
      setShowForm(false);
    } finally {
      setSaving(false);
    }
  };

  const toggleActive = async (coach: Coach) => {
    await updateDoc(doc(db, 'coaches', coach.id), { active: !coach.active });
  };

  const handleDelete = async (coach: Coach) => {
    if (!confirm(`Eliminar a ${coach.name}? Esta accion no se puede deshacer.`)) return;
    await deleteDoc(doc(db, 'coaches', coach.id));
  };

  return (
    <div>
      <div className="page-header">
        <h1>Profesores</h1>
        <button className="btn" onClick={openCreate}>+ Nuevo profesor</button>
      </div>

      <div className="card" style={{ padding: 0 }}>
        {loading ? (
          <p style={{ padding: 20 }}>Cargando...</p>
        ) : coaches.length === 0 ? (
          <p className="empty-state">Aun no hay profesores registrados.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Nombre</th>
                <th>Contacto</th>
                <th>Especialidad</th>
                <th>Estado</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {coaches.map((coach) => (
                <tr key={coach.id}>
                  <td>{coach.name}</td>
                  <td>
                    {coach.phone && <div>{coach.phone}</div>}
                    {coach.email && <div style={{ color: 'var(--color-text-muted)' }}>{coach.email}</div>}
                  </td>
                  <td>{SPECIALTY_LABEL[coach.specialty]}</td>
                  <td>
                    <span className={coach.active ? 'badge badge-open' : 'badge badge-cancelled'}>
                      {coach.active ? 'Activo' : 'Inactivo'}
                    </span>
                  </td>
                  <td style={{ display: 'flex', gap: 8 }}>
                    <button className="btn-secondary btn" onClick={() => openEdit(coach)}>Editar</button>
                    <button className="btn-secondary btn" onClick={() => toggleActive(coach)}>
                      {coach.active ? 'Desactivar' : 'Activar'}
                    </button>
                    <button className="btn-danger btn" onClick={() => handleDelete(coach)}>Eliminar</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {showForm && (
        <Modal title={editing ? 'Editar profesor' : 'Nuevo profesor'} onClose={() => setShowForm(false)}>
          <form onSubmit={handleSave}>
            <div className="field">
              <label>Nombre completo</label>
              <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            </div>
            <div className="field">
              <label>Telefono</label>
              <input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
            </div>
            <div className="field">
              <label>Correo</label>
              <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
            </div>
            <div className="field">
              <label>Foto (URL)</label>
              <input value={form.photoUrl} onChange={(e) => setForm({ ...form, photoUrl: e.target.value })} />
            </div>
            <div className="field">
              <label>Especialidad</label>
              <select
                value={form.specialty}
                onChange={(e) => setForm({ ...form, specialty: e.target.value as CoachSpecialty })}
              >
                <option value="ambas">Particulares y grupales</option>
                <option value="individual">Solo clases particulares</option>
                <option value="grupal">Solo clases grupales</option>
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
