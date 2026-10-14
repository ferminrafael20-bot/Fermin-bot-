import React, { useEffect, useState } from 'react';
import { addDoc, collection, deleteDoc, doc, onSnapshot, updateDoc } from 'firebase/firestore';
import { db } from '@/firebase/config';
import { AffiliatedBrand } from '@/types';
import Modal from '@/components/Modal';

const EMPTY_FORM = { name: '', code: '', discountPercent: 10, description: '', logoUrl: '' };

export default function DescuentosPage() {
  const [brands, setBrands] = useState<AffiliatedBrand[]>([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState<AffiliatedBrand | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const unsubscribe = onSnapshot(collection(db, 'affiliatedBrands'), (snap) => {
      setBrands(snap.docs.map((d) => ({ id: d.id, ...d.data() } as AffiliatedBrand)));
      setLoading(false);
    });
    return unsubscribe;
  }, []);

  const openCreate = () => {
    setEditing(null);
    setForm(EMPTY_FORM);
    setShowForm(true);
  };

  const openEdit = (brand: AffiliatedBrand) => {
    setEditing(brand);
    setForm({
      name: brand.name,
      code: brand.code,
      discountPercent: brand.discountPercent,
      description: brand.description ?? '',
      logoUrl: brand.logoUrl ?? '',
    });
    setShowForm(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      if (editing) {
        await updateDoc(doc(db, 'affiliatedBrands', editing.id), { ...form });
      } else {
        await addDoc(collection(db, 'affiliatedBrands'), { ...form });
      }
      setShowForm(false);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (brand: AffiliatedBrand) => {
    if (!confirm(`Eliminar la marca afiliada "${brand.name}"?`)) return;
    await deleteDoc(doc(db, 'affiliatedBrands', brand.id));
  };

  return (
    <div>
      <div className="page-header">
        <h1>Descuentos exclusivos</h1>
        <button className="btn" onClick={openCreate}>+ Nueva marca afiliada</button>
      </div>
      <p style={{ color: 'var(--color-text-muted)', fontSize: 13, marginTop: -8 }}>
        Estas marcas y codigos se muestran a los usuarios suscritos en la pestana "Suscripcion" de la app.
        Los planes de suscripcion (Basico/Plus/Pro) y su % de descuento en clases estan definidos en el
        backend (functions/src/subscriptions.ts) -- pide un ajuste si quieres administrarlos desde aqui tambien.
      </p>

      <div className="card" style={{ padding: 0 }}>
        {loading ? (
          <p style={{ padding: 20 }}>Cargando...</p>
        ) : brands.length === 0 ? (
          <p className="empty-state">Aun no hay marcas afiliadas.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Marca</th>
                <th>Codigo</th>
                <th>Descuento</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {brands.map((brand) => (
                <tr key={brand.id}>
                  <td>{brand.name}</td>
                  <td>{brand.code}</td>
                  <td>{brand.discountPercent}%</td>
                  <td style={{ display: 'flex', gap: 8 }}>
                    <button className="btn-secondary btn" onClick={() => openEdit(brand)}>Editar</button>
                    <button className="btn-danger btn" onClick={() => handleDelete(brand)}>Eliminar</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {showForm && (
        <Modal title={editing ? 'Editar marca' : 'Nueva marca afiliada'} onClose={() => setShowForm(false)}>
          <form onSubmit={handleSave}>
            <div className="field">
              <label>Nombre de la marca</label>
              <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            </div>
            <div className="field">
              <label>Codigo de descuento</label>
              <input required value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} />
            </div>
            <div className="field">
              <label>% de descuento</label>
              <input
                type="number"
                min={1}
                max={100}
                required
                value={form.discountPercent}
                onChange={(e) => setForm({ ...form, discountPercent: Number(e.target.value) })}
              />
            </div>
            <div className="field">
              <label>Descripcion (opcional)</label>
              <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
            </div>
            <div className="field">
              <label>Logo (URL, opcional)</label>
              <input value={form.logoUrl} onChange={(e) => setForm({ ...form, logoUrl: e.target.value })} />
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
