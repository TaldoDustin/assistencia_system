import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "sonner";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
import Layout from "@/components/Layout";
import Login from "@/pages/Login";
import Dashboard from "@/pages/Dashboard";
import Orders from "@/pages/Orders";
import NewOrder from "@/pages/NewOrder";
import EditOrder from "@/pages/EditOrder";
import Kanban from "@/pages/Kanban";
import Garantias from "@/pages/Garantias";
import Stock from "@/pages/Stock";
import RepairTypes from "@/pages/RepairTypes";
import PriceTables from "@/pages/PriceTables";
import OperationalCosts from "@/pages/OperationalCosts";
import Reports from "@/pages/Reports";
import Users from "@/pages/Users";
import { Loader2 } from "lucide-react";

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<Dashboard />} />
        <Route path="/ordens" element={<Orders />} />
        <Route path="/ordens/nova" element={<NewOrder />} />
        <Route path="/ordens/editar/:id" element={<EditOrder />} />
        <Route path="/kanban" element={<Kanban />} />
        <Route path="/garantias" element={<Garantias />} />
        <Route path="/estoque" element={<Stock />} />
        <Route path="/reparos" element={<RepairTypes />} />
        <Route path="/precos" element={<PriceTables />} />
        <Route path="/custos" element={<OperationalCosts />} />
        <Route path="/relatorios" element={<Reports />} />
        <Route path="/usuarios" element={<Users />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter basename="/app">
      <AuthProvider>
        <Toaster position="top-right" richColors />
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}
