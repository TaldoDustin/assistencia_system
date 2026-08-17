import { motion, useReducedMotion } from "motion/react";

const MotionDiv = motion.div;

// Entrada de seção ao rolar, reaproveitada em toda a Landing Page — evita repetir a
// mesma configuração de whileInView em cada um dos 14 componentes de seção.
export function FadeInSection({ children, className, delay = 0, ...props }) {
  const reducedMotion = useReducedMotion();

  return (
    <MotionDiv
      className={className}
      initial={reducedMotion ? undefined : { opacity: 0, y: 24 }}
      whileInView={reducedMotion ? undefined : { opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-80px" }}
      transition={{ duration: 0.3, ease: "easeOut", delay }}
      {...props}
    >
      {children}
    </MotionDiv>
  );
}
