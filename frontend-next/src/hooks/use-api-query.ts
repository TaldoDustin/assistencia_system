"use client";

import { useEffect, useState } from "react";

interface QueryState<T> {
  key: string;
  data: T | null;
  error: string | null;
}

interface UseApiQueryResult<T> {
  data: T | null;
  error: string | null;
  loading: boolean;
}

/**
 * Hook de leitura para os endpoints do Flask (via proxy de dev, ver next.config.ts).
 *
 * Deriva `loading` comparando a `key` atual com a key do último resultado
 * aplicado, em vez de chamar setState de forma síncrona no corpo do efeito —
 * evita o cascading render que a regra `react-hooks/set-state-in-effect`
 * (eslint-plugin-react-hooks v7, ver ADR-012/Sprint Next.js) sinaliza. Todo
 * setState aqui acontece dentro do callback assíncrono (.then/.catch).
 *
 * `fetcher` deve ser estável (envolva com `useCallback` no chamador, com as
 * mesmas dependências que compõem `key`) para que o efeito só refaça a
 * chamada quando a consulta realmente muda.
 */
export function useApiQuery<T>(key: string, fetcher: () => Promise<T>): UseApiQueryResult<T> {
  const [state, setState] = useState<QueryState<T>>({ key: "", data: null, error: null });

  useEffect(() => {
    let cancelled = false;

    fetcher()
      .then((data) => {
        if (!cancelled) setState({ key, data, error: null });
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setState({
            key,
            data: null,
            error: err instanceof Error ? err.message : "Erro inesperado.",
          });
        }
      });

    return () => {
      cancelled = true;
    };
  }, [key, fetcher]);

  const isCurrent = state.key === key;
  return {
    data: isCurrent ? state.data : null,
    error: isCurrent ? state.error : null,
    loading: !isCurrent,
  };
}
