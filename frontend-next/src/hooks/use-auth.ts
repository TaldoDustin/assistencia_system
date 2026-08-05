"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { ApiError, getMe } from "@/lib/api";
import type { Usuario } from "@/lib/types";

interface UseAuthResult {
  usuario: Usuario | null;
  loading: boolean;
}

/**
 * Verifica a sessão Flask atual via GET /api/auth/me (same-origin, através do
 * proxy de dev do Next.js). Se não autenticado, redireciona para /login.
 * Protótipo somente-leitura — não há criação de sessão além do login existente.
 */
export function useAuth(): UseAuthResult {
  const router = useRouter();
  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelado = false;

    getMe()
      .then((u) => {
        if (!cancelado) {
          setUsuario(u);
          setLoading(false);
        }
      })
      .catch((error) => {
        if (cancelado) return;
        setLoading(false);
        if (error instanceof ApiError && error.status === 401) {
          router.replace("/login");
        }
      });

    return () => {
      cancelado = true;
    };
  }, [router]);

  return { usuario, loading };
}
