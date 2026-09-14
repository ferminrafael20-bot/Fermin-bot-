import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import { useAuth } from '@/context/AuthContext';

export default function Layout() {
  const { profile, signOut } = useAuth();

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <Sidebar />
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <header
          style={{
            display: 'flex',
            justifyContent: 'flex-end',
            alignItems: 'center',
            gap: 12,
            padding: '12px 24px',
            borderBottom: '1px solid var(--color-border)',
            background: '#fff',
          }}
        >
          <span style={{ fontSize: 13, color: 'var(--color-text-muted)' }}>
            {profile?.name} · {profile?.role}
          </span>
          <button className="btn-secondary btn" onClick={signOut}>
            Cerrar sesion
          </button>
        </header>
        <main style={{ flex: 1, padding: 24 }}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
