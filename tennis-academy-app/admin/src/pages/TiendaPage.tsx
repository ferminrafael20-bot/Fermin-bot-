import React, { useEffect, useState } from 'react';
import { collection, deleteDoc, doc, onSnapshot, orderBy, query } from 'firebase/firestore';
import { db } from '@/firebase/config';
import { Product } from '@/types';
import { refreshStoreProducts } from '@/services/api';

export default function TiendaPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('raqueta de tenis');
  const [refreshing, setRefreshing] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    const q = query(collection(db, 'products'), orderBy('lastScrapedAt', 'desc'));
    const unsubscribe = onSnapshot(q, (snap) => {
      setProducts(snap.docs.map((d) => ({ id: d.id, ...d.data() } as Product)));
      setLoading(false);
    });
    return unsubscribe;
  }, []);

  const handleRefresh = async () => {
    if (!searchTerm.trim()) return;
    setRefreshing(true);
    setMessage(null);
    try {
      const { data } = await refreshStoreProducts({ query: searchTerm.trim() });
      setMessage(`Se actualizaron ${data.added} productos para "${searchTerm}".`);
    } catch (err: any) {
      setMessage(err?.message ?? 'No se pudo actualizar el catalogo.');
    } finally {
      setRefreshing(false);
    }
  };

  const handleDelete = async (product: Product) => {
    if (!confirm(`Quitar "${product.title}" de la tienda?`)) return;
    await deleteDoc(doc(db, 'products', product.id));
  };

  return (
    <div>
      <div className="page-header">
        <h1>Tienda</h1>
      </div>

      <div className="card">
        <p style={{ marginTop: 0, color: 'var(--color-text-muted)', fontSize: 13 }}>
          Trae productos nuevos desde Mercado Libre buscando por termino. El catalogo tambien
          se actualiza solo una vez al dia con las categorias por defecto.
        </p>
        <div style={{ display: 'flex', gap: 8 }}>
          <input
            style={{ flex: 1, padding: '8px 10px', border: '1px solid var(--color-border)', borderRadius: 6 }}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Ej: raqueta de tenis"
          />
          <button className="btn" onClick={handleRefresh} disabled={refreshing}>
            {refreshing ? 'Buscando...' : 'Actualizar catalogo'}
          </button>
        </div>
        {message && <p style={{ fontSize: 13, marginTop: 8 }}>{message}</p>}
      </div>

      <div className="card" style={{ padding: 0 }}>
        {loading ? (
          <p style={{ padding: 20 }}>Cargando...</p>
        ) : products.length === 0 ? (
          <p className="empty-state">Todavia no hay productos. Usa el buscador de arriba.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th></th>
                <th>Producto</th>
                <th>Categoria</th>
                <th>Precio</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {products.map((product) => (
                <tr key={product.id}>
                  <td>
                    <img src={product.imageUrl} alt="" style={{ width: 48, height: 48, objectFit: 'cover', borderRadius: 6 }} />
                  </td>
                  <td>
                    <a href={product.mlUrl} target="_blank" rel="noreferrer">{product.title}</a>
                  </td>
                  <td>{product.category}</td>
                  <td>{product.currency} {product.price.toLocaleString('es-CL')}</td>
                  <td>
                    <button className="btn-danger btn" onClick={() => handleDelete(product)}>Quitar</button>
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
