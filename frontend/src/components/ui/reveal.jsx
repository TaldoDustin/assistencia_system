import { motion, useReducedMotion } from "motion/react";

const MotionDiv = motion.div;

/**
 * Entrada discreta para conteúdo que aparece após carregar (linhas de tabela, cards, estados
 * vazio/erro) — respeita `useReducedMotion`. Distinto de `components/landing/FadeInSection.jsx`
 * (que anima ao rolar, `whileInView`, específico da Landing): este componente anima na montagem
 * (`animate`), pensado para conteúdo de página autenticada carregado via fetch. Ver
 * `ENGINEERING_GUIDE.md` §3.2 para quando usar Motion vs. transição CSS — este componente é para
 * elementos React puros sem `Portal` do Radix por trás.
 * @param {{ children: import("react").ReactNode, className?: string, delay?: number }} props
 */
export function Reveal({ children, className, delay = 0, ...props }) {
  const reducedMotion = useReducedMotion();

  return (
    <MotionDiv
      className={className}
      initial={reducedMotion ? undefined : { opacity: 0, y: 8 }}
      animate={reducedMotion ? undefined : { opacity: 1, y: 0 }}
      transition={{ duration: 0.2, ease: "easeOut", delay }}
      {...props}
    >
      {children}
    </MotionDiv>
  );
}
