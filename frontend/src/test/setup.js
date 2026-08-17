import { afterEach } from "vitest";
import { cleanup } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";

// Cleanup automatico entre testes. @testing-library/react só se auto-registra
// quando `afterEach` é global (vitest.config.js aqui usa globals:false, para
// não exigir configuração extra de ESLint) - registrado explicitamente aqui,
// um único ponto, em vez de repetir em cada arquivo de teste.
afterEach(() => {
  cleanup();
});

// jsdom nao implementa matchMedia - necessario para o hook useIsMobile()
// (frontend/src/hooks/use-mobile.js), chamado incondicionalmente pelo
// SidebarProvider em qualquer teste que renderize o Shell.
if (typeof window !== "undefined" && !window.matchMedia) {
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: (query) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => false,
    }),
  });
}

// jsdom nao implementa IntersectionObserver - necessario para o whileInView do Motion
// (frontend/src/components/landing/FadeInSection.jsx), usado em toda a Landing Page.
if (typeof window !== "undefined" && !window.IntersectionObserver) {
  class IntersectionObserverStub {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
  window.IntersectionObserver = IntersectionObserverStub;
  global.IntersectionObserver = IntersectionObserverStub;
}
