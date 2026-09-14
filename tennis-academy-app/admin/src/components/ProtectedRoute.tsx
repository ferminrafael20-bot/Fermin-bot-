import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { firebaseUser, authorized, loading, signOut } = useAuth();

  if (loading || authorized === null) {
    return <div style={{ padding: 40 }}>Cargando...</div>;
  }

  if (!firebaseUser) {
    return <Navigate to="/login" replace />;
  }

  if (!authorized) {
    return (
      <div style={{ padding: 40 }}>
        <h2>No autorizado</h2>
        <p>Tu cuenta no tiene permisos de administrador o profesor.</p>
        <button className="btn" onClick={signOut}>
          Cerrar sesion
        </button>
      </div>
    );
  }

  return <>{children}</>;
}
