import { describe, expect, it } from "vitest";
import {
  cookieDeLogin,
  emitirToken,
  lerCookie,
  papelDaSenha,
  verificarToken,
} from "../lib/auth.js";

const env = { senhaGeral: "1234", senhaEstoque: "9876", signingSecret: "s3gr3d0-de-teste-bem-longo" };

describe("papelDaSenha", () => {
  it("mapeia cada senha ao papel certo", () => {
    expect(papelDaSenha("1234", env)).toBe("geral");
    expect(papelDaSenha("9876", env)).toBe("estoque");
  });
  it("senha errada → null", () => {
    expect(papelDaSenha("0000", env)).toBeNull();
    expect(papelDaSenha("", env)).toBeNull();
  });
});

describe("token de sessão", () => {
  it("round-trip preserva o papel", () => {
    const t = emitirToken("estoque", env.signingSecret);
    expect(verificarToken(t, env.signingSecret)).toBe("estoque");
  });
  it("assinatura errada → null", () => {
    const t = emitirToken("estoque", env.signingSecret);
    expect(verificarToken(t, "outro-segredo")).toBeNull();
  });
  it("token adulterado → null", () => {
    const t = emitirToken("geral", env.signingSecret);
    const [b, m] = t.split(".");
    const forjado = Buffer.from(JSON.stringify({ role: "estoque", exp: 9e12 })).toString("base64url");
    expect(verificarToken(`${forjado}.${m}`, env.signingSecret)).toBeNull();
    expect(verificarToken(`${b}.`, env.signingSecret)).toBeNull();
  });
  it("token expirado → null", () => {
    const passado = Date.now() - 1000 * 60 * 60 * 24;
    const t = emitirToken("geral", env.signingSecret, passado);
    expect(verificarToken(t, env.signingSecret)).toBeNull();
  });
});

describe("cookie", () => {
  it("cookieDeLogin tem flags de segurança", () => {
    const c = cookieDeLogin("abc");
    expect(c).toMatch(/HttpOnly/);
    expect(c).toMatch(/Secure/);
    expect(c).toMatch(/SameSite=Lax/);
  });
  it("lerCookie extrai o valor", () => {
    expect(lerCookie("a=1; sess=xyz.abc; b=2", "sess")).toBe("xyz.abc");
    expect(lerCookie(undefined, "sess")).toBeUndefined();
  });
});
