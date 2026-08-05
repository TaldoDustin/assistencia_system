import * as React from "react"

const MOBILE_BREAKPOINT = 768

export function useIsMobile() {
  // Valor inicial computado de forma lazy (durante a renderização), não em um
  // efeito — evita a regra react-hooks/set-state-in-effect. `window` só existe
  // no cliente; SSR cai no fallback `false`, igual ao comportamento anterior
  // (`!!undefined`).
  const [isMobile, setIsMobile] = React.useState<boolean>(() =>
    typeof window === "undefined" ? false : window.innerWidth < MOBILE_BREAKPOINT
  )

  React.useEffect(() => {
    const mql = window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT - 1}px)`)
    const onChange = () => {
      setIsMobile(window.innerWidth < MOBILE_BREAKPOINT)
    }
    mql.addEventListener("change", onChange)
    return () => mql.removeEventListener("change", onChange)
  }, [])

  return isMobile
}
