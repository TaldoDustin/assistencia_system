import { useEffect, useRef } from "react";

// UX-001 -- Preservação de Contexto da Navegação (docs/product/PRODUCT_BACKLOG.md).
// Mecanismo reutilizável: qualquer página de listagem pode salvar seu estado
// (filtros, busca, paginação, item em foco + posição de rolagem) antes de
// navegar para uma tela de visualização/edição/criação, e restaurar tudo ao
// voltar -- sem precisar localizar de novo o registro numa lista extensa.
const PREFIX = "nav_context:";

function chave(key) {
  return `${PREFIX}${key}`;
}

/**
 * Grava o snapshot de navegação de uma listagem, junto da posição de
 * rolagem no momento da chamada. Chamar antes de navegar para fora da
 * listagem (editar, ver detalhe, criar).
 */
export function saveListContext(key, snapshot) {
  try {
    sessionStorage.setItem(chave(key), JSON.stringify({ ...snapshot, scrollY: window.scrollY }));
  } catch {
    // sessionStorage indisponível (modo privado, quota excedida) -- falha
    // silenciosa: preservar contexto é conveniência, nunca pode quebrar a
    // navegação em si.
  }
}

/** Lê o snapshot salvo para `key`, ou `null` se não houver nenhum. */
export function readListContext(key) {
  try {
    const raw = sessionStorage.getItem(chave(key));
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

/**
 * Remove o snapshot salvo -- chamar quando o usuário inicia uma navegação
 * "nova" a partir da listagem (ex.: botão "Nova OS"), para não herdar
 * filtro/posição de uma sessão anterior por engano.
 */
export function clearListContext(key) {
  try {
    sessionStorage.removeItem(chave(key));
  } catch {
    // ignore
  }
}

/**
 * Restaura a posição de rolagem assim que a listagem termina de carregar
 * (`pronto === true`). Se o snapshot tiver `focusId`, tenta primeiro rolar
 * até a linha marcada com `data-context-row={focusId}` no DOM e aplica um
 * destaque temporário (classe `nav-context-highlight`, ver `index.css`);
 * sem essa linha (item não está mais na página atual, foi removido etc.),
 * cai para a posição de scroll salva. Roda uma única vez por montagem e
 * consome o snapshot (`clearListContext`) -- uma visita normal e posterior à
 * mesma listagem não deve reaplicar uma posição/destaque antigos.
 */
export function useRestoreScroll(key, pronto) {
  const restaurado = useRef(false);

  useEffect(() => {
    if (!pronto || restaurado.current) return;
    restaurado.current = true;

    const ctx = readListContext(key);
    if (!ctx) return;
    clearListContext(key);

    requestAnimationFrame(() => {
      if (ctx.focusId != null) {
        const el = document.querySelector(`[data-context-row="${ctx.focusId}"]`);
        if (el) {
          el.scrollIntoView({ behavior: "instant", block: "center" });
          el.classList.add("nav-context-highlight");
          setTimeout(() => el.classList.remove("nav-context-highlight"), 2000);
          return;
        }
      }
      if (typeof ctx.scrollY === "number") {
        window.scrollTo(0, ctx.scrollY);
      }
    });
  }, [key, pronto]);
}
