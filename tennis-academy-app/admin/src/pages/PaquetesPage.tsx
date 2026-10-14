import React, { useEffect, useState } from 'react';
import { addDoc, collection, deleteDoc, doc, onSnapshot, updateDoc } from 'firebase/firestore';
import { db } from '@/firebase/config';
import { ClassPackage } from '@/types';
import Modal from '@/components/Modal';

const EMPTY_FORM = {
  name: '',
  classCount: 4,
  price: 0,
  validityDays: 60,
  description: '',
  active: true,
};

export default function PaquetesPage() {
  const [packages, setPackages] = useState<ClassPackage[]>([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState<ClassPackage | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const unsubscribe = onSnapshot(collection(db, 'classPackages'), (snap) => {
      setPackages(snap.docs.map((d) => ({ id: d.id, ...d.data() } as ClassPackage)));
      setLoading(false);
    });
    return unsubscribe;
  }, []);

  const openCreate = () => {
    setEditing(null);
    setForm(EMPTY_FORM);
    setShowForm(true);
  };

  const openEdit = (pkg: ClassPackage) => {
    setEditing(pkg);
    setForm({
      name: pkg.name,
      classCount: pkg.classCount,
      price: pkg.price,
      validityDays: pkg.validityDays,
      description: pkg.description ?? '',
      active: pkg.active,
    });
    setShowForm(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      if (editing) {
        await updateDoc(doc(db, 'classPackages', editing.id), { ...form });
      } else {
        await addDoc(collection(db, 'classPackages'), { ...form });
      }
      setShowForm(false);
    } finally {
      setSaving(false);
    }
  };

  const handleToggleActive = async (pkg: ClassPackage) => {
    await updateDoc(doc(db, 'classPackages', pkg.id), { active: !pkg.active });
  };

  const handleDelete = async (pkg: ClassPackage) => {
    if (!confirm(`Eliminar el paquete "${pkg.name}"? Esto no afecta los paquetes que ya compraron los alumnos.`)) return;
    await deleteDoc(doc(db, 'classPackages', pkg.id));
  };

  return (
    <div>
      <div className="page-header">
        <h1>Paquetes de clases</h1>
        <button className="btn" onClick={openCreate}>+ Nuevo paquete</button>
      </div>
      <p style={{ color: 'var(--color-text-muted)', fontSize: 13, marginTop: -8 }}>
        Un paquete se paga una sola vez y le da al alumno un numero fijo de clases para agendar cuando
        quiera (eligiendo dia y horario entre las clases particulares abiertas), hasta que se le acaben
        los creditos o se venza el plazo de validez.
      </p>

      <div className="card" style={{ padding: 0 }}>
        {loading ? (
          <p style={{ padding: 20 }}>Cargando...</p>
        ) : packages.length === 0 ? (
          <p className="empty-state">Aun no hay paquetes de clases creados.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Paquete</th>
                <th>Clases</th>
                <th>Precio</th>
                <th>Validez</th>
                <th>Estado</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {packages.map((pkg) => (
                <tr key={pkg.id}>
                  <td>{pkg.name}</td>
                  <td>{pkg.classCount}</td>
                  <td>${pkg.price.toLocaleString('es-CL')}</td>
                  <td>{pkg.validityDays} dias</td>
                  <td><span className={`badge badge-${pkg.active ? 'open' : 'cancelled'}`}>{pkg.active ? 'activo' : 'oculto'}</span></td>
                  <td style={{ display: 'flex', gap: 8 }}>
                    <button className="btn-secondary btn" onClick={() => openEdit(pkg)}>Editar</button>
                    <button className="btn-secondary btn" onClick={() => handleToggleActive(pkg)}>
                      {pkg.active ? 'Ocultar' : 'Mostrar'}
                    </button>
                    <button className="btn-danger btn" onClick={() => handleDelete(pkg)}>Eliminar</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {showForm && (
        <Modal title={editing ? 'Editar paquete' : 'Nuevo paquete de clases'} onClose={() => setShowForm(false)}>
          <form onSubmit={handleSave}>
            <div className="field">
              <label>Nombre del paquete</label>
              <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            </div>
            <div style={{ display: 'flex', gap: 12 }}>
              <div className="field" style={{ flex: 1 }}>
                <label>Cantidad de clases</label>
                <input
                  type="number"
                  min={1}
                  required
                  value={form.classCount}
                  onChange={(e) => setForm({ ...form, classCount: Number(e.target.value) })}
                />
              </div>
              <div className="field" style={{ flex: 1 }}>
                <label>Precio (CLP)</label>
                <input
                  type="number"
                  min={0}
                  required
                  value={form.price}
                  onChange={(e) => setForm({ ...form, price: Number(e.target.value) })}
                />
              </div>
            </div>
            <div className="field">
              <label>Dias de validez desde la compra</label>
              <input
                type="number"
                min={1}
                required
                value={form.validityDays}
                onChange={(e) => setForm({ ...form, validityDays: Number(e.target.value) })}
              />
            </div>
            <div className="field">
              <label>Descripcion (opcional)</label>
              <textarea
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
              />
            </div>
            <div className="field">
              <label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <input
                  type="checkbox"
                  checked={form.active}
                  onChange={(e) => setForm({ ...form, active: e.target.checked })}
                />
                Visible para los alumnos en la app
              </label>
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
