/**
 * IR Flow API Client
 * Talks to Flask backend at /api/*.
 * Uses session cookies — credentials: 'include' on every request.
 * In Vite dev mode, the proxy in vite.config.js forwards /api → http://localhost:5080.
 */

const BASE = "/api";

function expandPieceMap(pecas = {}) {
  return Object.entries(pecas).flatMap(([id, quantidade]) => {
    const itemId = Number.parseInt(id, 10);
    const total = Number.parseInt(quantidade, 10);
    if (!Number.isInteger(itemId) || !Number.isInteger(total) || total <= 0) {
      return [];
    }
    return Array.from({ length: total }, () => itemId);
  });
}

function normalizeStockResponse(data) {
  if (data?.ok && data.itens && !data.items) {
    return { ...data, items: data.itens };
  }
  return data;
}

function normalizeWarrantyResponse(data) {
  if (!data?.ok || !data.ordens) {
    return data;
  }

  const garantias = data.ordens.map((item) => {
    const color = item.garantia?.color;
    const statusMap = {
      green: "ativa",
      amber: "vencendo",
      red: "vencida",
    };

    return {
      ...item,
      reparos_texto: (item.reparos || []).join(", "),
      dias_restantes: item.garantia?.dias_restantes,
      status_garantia: statusMap[color] || "desconhecida",
    };
  });

  return { ...data, garantias };
}

function normalizeCostsResponse(data) {
  if (data?.ok && data.itens && !data.custos) {
    return { ...data, custos: data.itens };
  }
  return data;
}

function withPieceIds(data) {
  if (!data || !data.pecas) {
    return data;
  }

  const { pecas, ...rest } = data;
  return {
    ...rest,
    pecas_ids: expandPieceMap(pecas),
  };
}

async function request(method, path, body) {
  const opts = {
    method,
    credentials: "include",
    headers: {},
  };
  if (body !== undefined) {
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(body);
  }
  const res = await fetch(`${BASE}${path}`, opts);
  const data = await res.json().catch(() => ({}));
  return data;
}

const get  = (path)        => request("GET",    path);
const post = (path, body)  => request("POST",   path, body);
const put  = (path, body)  => request("PUT",    path, body);
const del  = (path)        => request("DELETE", path);

// ── Auth ────────────────────────────────────────────────────────────────────
export const auth = {
  login:  (usuario, senha) => post("/auth/login",  { usuario, senha }),
  logout: ()               => post("/auth/logout"),
  me:     ()               => get("/auth/me"),
};

// ── Constants ───────────────────────────────────────────────────────────────
export const constantes = {
  get: () => get("/constantes"),
};

// ── Alerts ──────────────────────────────────────────────────────────────────
export const alertas = {
  list: () => get("/alertas"),
};

// ── Dashboard ───────────────────────────────────────────────────────────────
export const dashboard = {
  get: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return get(`/dashboard${qs ? "?" + qs : ""}`);
  },
};

// ── Ordens de Serviço ───────────────────────────────────────────────────────
export const ordens = {
  list:          (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return get(`/ordens${qs ? "?" + qs : ""}`);
  },
  get:           (id)         => get(`/ordens/${id}`),
  create:        (data)       => post("/ordens", withPieceIds(data)),
  update:        (id, data)   => put(`/ordens/${id}`, withPieceIds(data)),
  delete:        (id)         => del(`/ordens/${id}`),
  patchStatus:   (id, status) => request("PATCH", `/ordens/${id}/status`, { status }),
  clienteHistory:(nome)       => get(`/ordens/historico-cliente?cliente=${encodeURIComponent(nome)}`),
};

// ── Checklist de Aparelho ──────────────────────────────────────────────────
export const checklist = {
  getByOrder:       (orderId)     => get(`/ordens/${orderId}/checklist`),
  generateToken:    (orderId)     => post(`/ordens/${orderId}/checklist/token`),
  getPublic:        (token)       => get(`/checklist/${encodeURIComponent(token)}`),
  savePublic:       (token, data) => post(`/checklist/${encodeURIComponent(token)}`, data),
  publicUrl:        (token, baseUrl = "") => {
    const suffix = `/app/checklist/${encodeURIComponent(token)}`;
    return baseUrl ? `${baseUrl.replace(/\/$/, "")}${suffix}` : suffix;
  },
  qrImageUrl:       (url)         => `https://api.qrserver.com/v1/create-qr-code/?size=240x240&data=${encodeURIComponent(url)}`,
};

// ── Estoque ─────────────────────────────────────────────────────────────────
export const estoque = {
  list:   async (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return normalizeStockResponse(await get(`/estoque${qs ? "?" + qs : ""}`));
  },
  get:    (id)         => get(`/estoque/${id}`),
  create: (data)       => post("/estoque", data),
  update: (id, data)   => put(`/estoque/${id}`, data),
  delete: (id)         => del(`/estoque/${id}`),
};

// ── Reparos ─────────────────────────────────────────────────────────────────
export const reparos = {
  list:   ()          => get("/reparos"),
  create: (data)      => post("/reparos", data),
  update: (id, data)  => put(`/reparos/${id}`, data),
  delete: (id)        => del(`/reparos/${id}`),
};

// ── Custos Operacionais ──────────────────────────────────────────────────────
export const custos = {
  list:   async (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return normalizeCostsResponse(await get(`/custos${qs ? "?" + qs : ""}`));
  },
  create: (data)        => post("/custos", data),
  update: (id, data)    => put(`/custos/${id}`, data),
  delete: (id)          => del(`/custos/${id}`),
};

// ── Tabelas de Preço ─────────────────────────────────────────────────────────
export const precos = {
  list:   ()     => get("/precos"),
  save:   (data) => post("/precos", data),          // { tabela, servico, modelo, valor }
  remove: (data) => post("/precos/excluir", data),  // { tabela, servico, modelo }
  sugerir: (params) => {
    const qs = new URLSearchParams(params).toString();
    return get(`/precos/sugerir?${qs}`);
  },
};

// ── Garantias ────────────────────────────────────────────────────────────────
export const garantias = {
  list: async () => normalizeWarrantyResponse(await get("/garantias")),
};

// ── Relatórios ───────────────────────────────────────────────────────────────
export const relatorios = {
  irphones:  (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return get(`/relatorios/ir-phones${qs ? "?" + qs : ""}`);
  },
  tecnicos:  (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return get(`/relatorios/tecnicos${qs ? "?" + qs : ""}`);
  },
  pdfUrl:    (tipo, params = {}) => {
    const qs = new URLSearchParams(params).toString();
    const endpoint = tipo === "irphones" ? "ir-phones" : tipo;
    return `${BASE}/relatorios/pdf/${endpoint}${qs ? "?" + qs : ""}`;
  },
};

// ── Usuários ─────────────────────────────────────────────────────────────────
export const usuarios = {
  list:   ()          => get("/usuarios"),
  create: (data)      => post("/usuarios", data),
  update: (id, data)  => put(`/usuarios/${id}`, data),
  delete: (id)        => del(`/usuarios/${id}`),
};

// ── Backup ───────────────────────────────────────────────────────────────────
export const backup = {
  criar:    ()       => post("/backup/criar"),
  list:     ()       => get("/backup/listar"),
  download: (file)   => `${BASE}/backup/download/${encodeURIComponent(file)}`,
};
