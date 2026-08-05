"use client";

import { useSyncExternalStore } from "react";

function subscribe(): () => void {
  return () => {};
}

/**
 * Detecta se o componente já hidratou no cliente, sem usar useEffect+setState
 * (evita a regra react-hooks/set-state-in-effect). getServerSnapshot retorna
 * false (SSR/primeira renderização), getSnapshot retorna true — React
 * reconcilia a diferença com um re-render após a hidratação.
 */
export function useHasMounted(): boolean {
  return useSyncExternalStore(
    subscribe,
    () => true,
    () => false,
  );
}
