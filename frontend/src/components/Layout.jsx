import { Outlet, Link, useLocation, useNavigate } from "react-router-dom";
import { useState } from "react";
import {
  LayoutDashboard, ClipboardList, Package, Wrench, DollarSign,
  BarChart3, Menu, X, Kanban, Shield, Tag, Users, LogOut, User,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import GlobalAlerts from "./GlobalAlerts";
import { useAuth } from "@/contexts/AuthContext";

const navItems = [
  { path: "/",          label: "Dashboard",           icon: LayoutDashboard },
  { path: "/ordens",    label: "Ordens de Serviço",   icon: ClipboardList },
  { path: "/kanban",    label: "Kanban",               icon: Kanban },
  { path: "/garantias", label: "Garantias",            icon: Shield },
  { path: "/estoque",   label: "Estoque",              icon: Package },
  { path: "/reparos",   label: "Tipos de Reparo",      icon: Wrench },
  { path: "/precos",    label: "Tabelas de Preço",     icon: Tag },
  { path: "/custos",    label: "Custos Operacionais",  icon: DollarSign },
  { path: "/relatorios",label: "Relatórios",           icon: BarChart3 },
  { path: "/usuarios",  label: "Usuários",             icon: Users },
];

export default function Layout() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate("/login", { replace: true });
  };

  const SidebarContent = () => (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <div className="px-4 py-5 border-b border-sidebar-border">
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
            <span className="text-primary-foreground font-bold text-sm">IR</span>
          </div>
          <span className="font-semibold text-sidebar-foreground text-base">IR Flow</span>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto px-2 py-3 space-y-0.5">
        {navItems.map(({ path, label, icon: Icon }) => {
          const isActive = path === "/" ? location.pathname === "/" : location.pathname.startsWith(path);
          return (
            <Link
              key={path}
              to={path}
              onClick={() => setMobileOpen(false)}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? "bg-sidebar-primary text-sidebar-primary-foreground"
                  : "text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-foreground"
              }`}
            >
              <Icon className="h-4 w-4 shrink-0" />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-3 py-3 border-t border-sidebar-border space-y-2">
        {/* User info */}
        {user && (
          <div className="flex items-center gap-2 px-2 py-1.5">
            <div className="h-7 w-7 rounded-full bg-sidebar-accent flex items-center justify-center">
              <User className="h-4 w-4 text-sidebar-foreground/70" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-sidebar-foreground truncate">{user.nome || user.usuario}</p>
              <p className="text-xs text-sidebar-foreground/60 capitalize">{user.perfil}</p>
            </div>
          </div>
        )}
        <div className="flex items-center justify-between px-1">
          <span className="text-xs text-sidebar-foreground/60">v1.0.0</span>
          <div className="flex items-center gap-1">
            <GlobalAlerts />
            <Button
              variant="ghost"
              size="icon"
              onClick={handleLogout}
              className="h-8 w-8 text-sidebar-foreground/70 hover:text-sidebar-foreground hover:bg-sidebar-accent"
            >
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="flex min-h-screen bg-background">
      {/* Desktop sidebar */}
      <aside className="hidden lg:flex flex-col fixed left-0 top-0 h-full w-64 bg-sidebar text-sidebar-foreground border-r border-sidebar-border z-30">
        <SidebarContent />
      </aside>

      {/* Mobile top bar */}
      <div className="fixed top-0 left-0 right-0 h-14 bg-sidebar border-b border-sidebar-border flex items-center px-4 lg:hidden z-30">
        <button
          onClick={() => setMobileOpen(true)}
          className="h-8 w-8 flex items-center justify-center rounded-lg hover:bg-sidebar-accent"
        >
          <Menu className="h-5 w-5 text-sidebar-foreground" />
        </button>
        <span className="ml-3 font-semibold text-sidebar-foreground">IR Flow</span>
      </div>

      {/* Mobile drawer overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-black/60 z-40 lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Mobile drawer */}
      <aside
        className={`fixed left-0 top-0 h-full w-64 bg-sidebar text-sidebar-foreground border-r border-sidebar-border z-50 transition-transform lg:hidden ${
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="absolute right-3 top-3">
          <button
            onClick={() => setMobileOpen(false)}
            className="h-8 w-8 flex items-center justify-center rounded-lg hover:bg-sidebar-accent"
          >
            <X className="h-4 w-4 text-sidebar-foreground" />
          </button>
        </div>
        <SidebarContent />
      </aside>

      {/* Main content */}
      <main className="flex-1 lg:ml-64 pt-14 lg:pt-0 min-h-screen">
        <div className="p-4 lg:p-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
