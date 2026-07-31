import { lazy, Suspense } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "sonner";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
import Layout from "@/components/Layout";
import { Loader2 } from "lucide-react";

const Login = lazy(() => import("@/pages/Login"));
const ChecklistDevice = lazy(() => import("@/pages/ChecklistDevice"));
const Dashboard = lazy(() => import("@/pages/Dashboard"));
const Orders = lazy(() => import("@/pages/Orders"));
const NewOrder = lazy(() => import("@/pages/NewOrder"));
const EditOrder = lazy(() => import("@/pages/EditOrder"));
const Kanban = lazy(() => import("@/pages/Kanban"));
const ShoppingList = lazy(() => import("@/pages/ShoppingList"));
const Garantias = lazy(() => import("@/pages/Garantias"));
const Stock = lazy(() => import("@/pages/Stock"));
const Produtos = lazy(() => import("@/pages/Produtos"));
const Clientes = lazy(() => import("@/pages/Clientes"));
const Vendas = lazy(() => import("@/pages/Vendas"));
const VendaDetalhe = lazy(() => import("@/pages/VendaDetalhe"));
const UnidadesSerializadas = lazy(() => import("@/pages/UnidadesSerializadas"));
const Compras = lazy(() => import("@/pages/Compras"));
const RepairTypes = lazy(() => import("@/pages/RepairTypes"));
const TiposGarantia = lazy(() => import("@/pages/TiposGarantia"));
const PriceTables = lazy(() => import("@/pages/PriceTables"));
const OperationalCosts = lazy(() => import("@/pages/OperationalCosts"));
const Reports = lazy(() => import("@/pages/Reports"));
const Backup = lazy(() => import("@/pages/Backup"));
const Users = lazy(() => import("@/pages/Users"));

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
    <Suspense
      fallback={
        <div className="flex items-center justify-center min-h-screen">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      }
    >
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/checklist/:token" element={<ChecklistDevice />} />
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
          <Route path="/compras" element={<ShoppingList />} />
          <Route path="/kanban" element={<Kanban />} />
          <Route path="/garantias" element={<Garantias />} />
          <Route path="/clientes" element={<Clientes />} />
          <Route path="/vendas" element={<Vendas />} />
          <Route path="/vendas/:id" element={<VendaDetalhe />} />
          <Route path="/produtos" element={<Produtos />} />
          <Route path="/unidades-serializadas" element={<UnidadesSerializadas />} />
          <Route path="/estoque" element={<Stock />} />
          <Route path="/compras" element={<Compras />} />
          <Route path="/reparos" element={<RepairTypes />} />
          <Route path="/tipos-garantia" element={<TiposGarantia />} />
          <Route path="/precos" element={<PriceTables />} />
          <Route path="/custos" element={<OperationalCosts />} />
          <Route path="/relatorios" element={<Reports />} />
          <Route path="/backup" element={<Backup />} />
          <Route path="/usuarios" element={<Users />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Toaster position="top-right" richColors />
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}
