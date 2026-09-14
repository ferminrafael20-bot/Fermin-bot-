import React, { useEffect, useState } from 'react';
import { addDoc, collection, deleteDoc, doc, onSnapshot, updateDoc } from 'firebase/firestore';
import { db } from '@/firebase/config';
import { Level, TrainingGroup } from '@/types';
import { useCoaches } from '@/hooks/useCoaches';
import Modal from '@/components/Modal';

const EMPTY_FORM = {
  name: '',
  coachId: '',
  schedule: '',
  capacity: 8,
  monthlyPrice: 0,
  level: 'principiante' as Level,
};

export default function ClasesGrupalesPage() {
  const coaches = useCoaches();
  const [groups, setGroups] = useState<TrainingGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState<TrainingGroup | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const unsubscribe = onSnapshot(collection(db, 'trainingGroups'), (snap) => {
      setGroups(snap.docs.map((d) => ({ id: d.id, ...d.data() } as TrainingGroup)));
      setLoading(false);
    });
    return unsubscribe;
  }, []);

  const openCreate = () => {
    setEditing(null);
    setForm({ ...EMPTY_FORM, coachId: coaches[0]?.id ?? '' });
    setShowForm(true);
  };

  const openEdit = (group: TrainingGroup) => {
    setEditing(group);
    setForm({
      name: group.name,
      coachId: group.coachId,
      schedule: group.schedule,
      capacity: group.capacity,
      monthlyPrice: group.monthlyPrice,
      level: group.level,
    });
    setShowForm(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    const takenCount = editing ? editing.memberIds.length + (editing.pendingMemberIds ?? []).length : 0;
    if (form.capacity < takenCount) {
      alert(`No puedes bajar el cupo por debajo de ${takenCount} (ya hay alumnos anotados).`);
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
        await updateDoc(doc(db, 'trainingGroups', editing.id), payload);
      } else {
        await addDoc(collection(db, 'trainingGroups'), {
          ...payload,
          memberIds: [],
          pendingMemberIds: [],
        });
      }
      setShowForm(false);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (group: TrainingGroup) => {
    if (group.memberIds.length > 0) {
      alert('No puedes eliminar un grupo con alumnos activos.');
      return;
    }
    if (!confirm(`Eliminar el grupo "${group.name}"?`)) return;
    await deleteDoc(doc(db, 'trainingGroups', group.id));
  };

  return (
    <div>
      <div className="page-header">
        <h1>Clases grupales</h1>
        <button className="btn" onClick={openCreate} disabled={coaches.length === 0}>+ Nuevo grupo</button>
      </div>
      {coaches.length === 0 && (
        <p className="empty-state">Primero registra al menos un profesor en la seccion "Profesores".</p>
      )}

      <div className="card" style={{ padding: 0 }}>
        {loading ? (
          <p style={{ padding: 20 }}>Cargando...</p>
        ) : groups.length === 0 ? (
          <p className="empty-state">Aun no hay grupos de entrenamiento creados.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Grupo</th>
                <th>Horario</th>
                <th>Profesor</th>
                <th>Cupos</th>
                <th>Mensualidad</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {groups.map((group) => (
                <tr key={group.id}>
                  <td>{group.name} <span style={{ color: 'var(--color-text-muted)' }}>({group.level})</span></td>
                  <td>{group.schedule}</td>
                  <td>{group.coachName}</td>
                  <td>{group.memberIds.length}/{group.capacity}</td>
                  <td>${group.monthlyPrice.toLocaleString('es-CL')}</td>
                  <td style={{ display: 'flex', gap: 8 }}>
                    <button className="btn-secondary btn" onClick={() => openEdit(group)}>Editar</button>
                    <button className="btn-danger btn" onClick={() => handleDelete(group)}>Eliminar</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {showForm && (
        <Modal title={editing ? 'Editar grupo' : 'Nuevo grupo de entrenamiento'} onClose={() => setShowForm(false)}>
          <form onSubmit={handleSave}>
            <div className="field">
              <label>Nombre del grupo</label>
              <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
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
              <label>Horario (texto libre)</label>
              <input
                placeholder="Ej: Lun y Mie 18:00-19:30"
                required
                value={form.schedule}
                onChange={(e) => setForm({ ...form, schedule: e.target.value })}
              />
            </div>
            <div style={{ display: 'flex', gap: 12 }}>
              <div className="field" style={{ flex: 1 }}>
                <label>Cupos</label>
                <input type="number" min={1} required value={form.capacity} onChange={(e) => setForm({ ...form, capacity: Number(e.target.value) })} />
              </div>
              <div className="field" style={{ flex: 1 }}>
                <label>Mensualidad (CLP)</label>
                <input type="number" min={0} required value={form.monthlyPrice} onChange={(e) => setForm({ ...form, monthlyPrice: Number(e.target.value) })} />
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
