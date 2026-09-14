import React from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider } from '@/context/AuthContext';
import ProtectedRoute from '@/components/ProtectedRoute';
import Layout from '@/components/Layout';
import LoginPage from '@/pages/LoginPage';
import ClasesGrupalesPage from '@/pages/ClasesGrupalesPage';
import ClasesParticularesPage from '@/pages/ClasesParticularesPage';
import ProfesoresPage from '@/pages/ProfesoresPage';
import TiendaPage from '@/pages/TiendaPage';
import DescuentosPage from '@/pages/DescuentosPage';
import ReservasPage from '@/pages/ReservasPage';

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/clases/grupales" replace />} />
          <Route path="clases/grupales" element={<ClasesGrupalesPage />} />
          <Route path="clases/particulares" element={<ClasesParticularesPage />} />
          <Route path="profesores" element={<ProfesoresPage />} />
          <Route path="tienda" element={<TiendaPage />} />
          <Route path="descuentos" element={<DescuentosPage />} />
          <Route path="reservas" element={<ReservasPage />} />
        </Route>
      </Routes>
    </AuthProvider>
  );
}
