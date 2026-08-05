/**
 * Cliente de leitura para a API Flask do Fluxoly, via proxy de dev do Next.js
 * (ver next.config.ts). Todas as chamadas usam caminhos relativos ("/api/...")
 * para que o browser as trate como same-origin e envie o cookie de sessão do
 * Flask automaticamente — sem nenhuma configuração de CORS extra.
 *
 * Protótipo somente-leitura: nenhuma rota de mutação (POST/PUT/DELETE) além do
 * login/logout, exigidos apenas para autenticar contra a API real.
 */

import type {
  DashboardData,
  OrdemDetalheResponse,
  OrdensListaResponse,
  Usuario,
} from "./types";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

interface OkEnvelope {
  ok: boolean;
  erro?: string;
}

async function apiFetch<T extends OkEnvelope>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(path, {
    ...init,
    credentials: "include",
    headers: {
      Accept: "application/json",
      ...(init?.body ? { "Content-Type": "application/json" } : {}),
      ...init?.headers,
    },
  });

  let body: T;
  try {
    body = (await response.json()) as T;
  } catch {
    throw new ApiError(
      `Resposta inválida da API (status ${response.status}).`,
      response.status,
    );
  }

  if (!response.ok || body.ok === false) {
    throw new ApiError(body.erro || `Erro na API (status ${response.status}).`, response.status);
  }

  return body;
}

export async function login(usuario: string, senha: string): Promise<Usuario> {
  const data = await apiFetch<{ ok: boolean; usuario: Usuario }>(
    "/api/auth/login",
    {
      method: "POST",
      body: JSON.stringify({ usuario, senha }),
    },
  );
  return data.usuario;
}

export async function logout(): Promise<void> {
  await apiFetch<OkEnvelope>("/api/auth/logout", { method: "POST" });
}

export async function getMe(): Promise<Usuario> {
  const data = await apiFetch<{ ok: boolean; usuario: Usuario }>("/api/auth/me");
  return data.usuario;
}

export async function getDashboard(params?: {
  start_date?: string;
  end_date?: string;
  tecnico?: string;
}): Promise<DashboardData> {
  const query = new URLSearchParams();
  if (params?.start_date) query.set("start_date", params.start_date);
  if (params?.end_date) query.set("end_date", params.end_date);
  if (params?.tecnico) query.set("tecnico", params.tecnico);
  const qs = query.toString();
  const data = await apiFetch<{ ok: boolean } & DashboardData>(
    `/api/dashboard${qs ? `?${qs}` : ""}`,
  );
  return data;
}

export async function getOrdens(params?: {
  q?: string;
  status?: string;
}): Promise<OrdensListaResponse> {
  const query = new URLSearchParams();
  if (params?.q) query.set("q", params.q);
  if (params?.status) query.set("status", params.status);
  const qs = query.toString();
  return apiFetch<OrdensListaResponse>(`/api/ordens${qs ? `?${qs}` : ""}`);
}

export async function getOrdem(id: number | string): Promise<OrdemDetalheResponse> {
  return apiFetch<OrdemDetalheResponse>(`/api/ordens/${id}`);
}
