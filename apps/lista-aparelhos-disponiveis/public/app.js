/* Ferramenta interna "Lista de Aparelhos Disponíveis" — IR Phones.
   A página não carrega nenhum dado sensível: tudo vem de /api/inventory já filtrado por papel. */
(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const brl = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
  const REFRESH_MS = 5 * 60 * 1000;

  let estado = {
    papel: null,
    geradoEm: null,
    itens: [],          // aba corrente já normalizada
    aba: "disponiveis", // só usado no papel estoque
    respostaEstoque: null,
  };

  /* ---------------- Lock ---------------- */
  const lock = $("lock");
  const app = $("app");

  $("lockForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = $("lockBtn");
    const err = $("lockErr");
    err.hidden = true;
    btn.disabled = true;
    try {
      const r = await fetch("/api/session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ senha: $("senha").value }),
      });
      if (!r.ok) {
        const j = await r.json().catch(() => ({}));
        err.textContent = j.erro || "Não foi possível entrar.";
        err.hidden = false;
        return;
      }
      const j = await r.json();
      entrar(j.papel);
    } finally {
      btn.disabled = false;
      $("senha").value = "";
    }
  });

  async function entrar(papel) {
    estado.papel = papel;
    lock.hidden = true;
    app.hidden = false;
    $("tabs").hidden = papel !== "estoque";
    $("kValorWrap").hidden = papel !== "estoque";
    await carregar();
  }

  $("btnSair").addEventListener("click", async () => {
    await fetch("/api/session", { method: "DELETE" }).catch(() => {});
    location.reload();
  });

  /* ---------------- Carregar dados ---------------- */
  async function carregar() {
    setStatus("Carregando…");
    try {
      const r = await fetch("/api/inventory", { headers: { "Cache-Control": "no-store" } });
      if (r.status === 401) { location.reload(); return; }
      if (!r.ok) {
        const j = await r.json().catch(() => ({}));
        setStatus(j.erro || `Erro ${r.status}`, true);
        return;
      }
      const data = await r.json();
      estado.geradoEm = data.geradoEm;
      if (data.papel === "estoque") {
        estado.respostaEstoque = data;
        aplicarAba();
      } else {
        estado.itens = data.itens;
        render();
      }
      atualizarStamp();
    } catch {
      setStatus("Falha de rede.", true);
    }
  }

  $("btnAtualizar").addEventListener("click", carregar);
  setInterval(() => { if (!document.hidden && !app.hidden) carregar(); }, REFRESH_MS);
  document.addEventListener("visibilitychange", () => {
    if (!document.hidden && !app.hidden) carregar();
  });

  /* ---------------- Abas (estoque) ---------------- */
  $("tabs").addEventListener("click", (e) => {
    const b = e.target.closest(".tab");
    if (!b) return;
    document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("is-active", t === b));
    estado.aba = b.dataset.tab;
    aplicarAba();
  });

  function aplicarAba() {
    const d = estado.respostaEstoque;
    if (!d) return;
    estado.itens = estado.aba === "reservados" ? d.reservados : d.disponiveis;
    render();
  }

  /* ---------------- Filtros ---------------- */
  ["busca", "fTipo", "fEstado", "fArmazenamento"].forEach((id) =>
    $(id).addEventListener("input", render),
  );

  function preencherFiltros() {
    const fill = (id, vals) => {
      const el = $(id);
      const cur = el.value;
      const uniq = [...new Set(vals.filter(Boolean))].sort((a, b) => a.localeCompare(b, "pt-BR"));
      el.innerHTML =
        `<option value="">Todos</option>` +
        uniq.map((v) => `<option${v === cur ? " selected" : ""}>${escapeHtml(v)}</option>`).join("");
    };
    fill("fTipo", estado.itens.map((i) => i.tipoProduto));
    fill("fEstado", estado.itens.map((i) => i.estado));
    fill("fArmazenamento", estado.itens.map((i) => i.armazenamento));
  }

  function filtrar() {
    const q = norm($("busca").value);
    const t = $("fTipo").value, e = $("fEstado").value, a = $("fArmazenamento").value;
    return estado.itens.filter((i) => {
      if (t && i.tipoProduto !== t) return false;
      if (e && i.estado !== e) return false;
      if (a && (i.armazenamento || "") !== a) return false;
      if (!q) return true;
      return norm(`${i.idCurto} ${i.modelo} ${i.cor || ""} ${i.tipoProduto} ${i.estado}`).includes(q);
    });
  }

  /* ---------------- Render ---------------- */
  function render() {
    preencherFiltros();
    const linhas = filtrar();
    const ehEstoque = estado.papel === "estoque";
    const reservadosView = ehEstoque && estado.aba === "reservados";

    $("kTotal").textContent = String(estado.itens.length);
    $("kVisiveis").textContent = String(linhas.length);
    if (ehEstoque) {
      const soma = linhas.reduce((s, i) => s + (i.precoVenda || 0), 0);
      $("kValor").textContent = brl.format(soma);
    }

    // agrupar por modelo + estado
    const grupos = new Map();
    for (const it of linhas) {
      const k = `${it.modelo} · ${it.estado}`;
      (grupos.get(k) || grupos.set(k, []).get(k)).push(it);
    }

    const cont = $("grupos");
    if (!linhas.length) {
      cont.innerHTML = `<p class="status">${estado.itens.length ? "Nada no filtro." : "Sem aparelhos."}</p>`;
      return;
    }

    cont.innerHTML = [...grupos.entries()].map(([titulo, its]) => {
      const precos = its.map((i) => i.precoVenda).filter((v) => v != null);
      const faixa = precos.length
        ? (Math.min(...precos) === Math.max(...precos)
            ? brl.format(precos[0])
            : `${brl.format(Math.min(...precos))} – ${brl.format(Math.max(...precos))}`)
        : "sob consulta";
      return `
      <section class="grupo">
        <button class="grupo-head" type="button" aria-expanded="true">
          <h2>${escapeHtml(titulo)}</h2>
          <span class="cont">${its.length} un.</span>
          <span class="faixa">${faixa}</span>
        </button>
        <div class="grupo-tabela">
          <table>
            <thead><tr>
              <th>ID</th><th>Armazenam.</th><th>Cor</th><th>Bateria</th><th>Preço</th>
              ${ehEstoque ? "<th>Custo</th><th>Margem</th><th>Parado</th>" : ""}
              <th>Detalhes</th>
              ${ehEstoque ? "<th></th>" : ""}
            </tr></thead>
            <tbody>
              ${its.map((i) => linhaHtml(i, ehEstoque, reservadosView)).join("")}
            </tbody>
          </table>
        </div>
      </section>`;
    }).join("");

    cont.querySelectorAll(".grupo-head").forEach((h) =>
      h.addEventListener("click", () => {
        const tabela = h.nextElementSibling;
        const aberto = tabela.hidden;
        tabela.hidden = !aberto;
        h.setAttribute("aria-expanded", String(aberto));
      }),
    );
    cont.querySelectorAll("[data-reservar]").forEach((b) =>
      b.addEventListener("click", () => abrirReserva(Number(b.dataset.reservar))),
    );
    cont.querySelectorAll("[data-liberar]").forEach((b) =>
      b.addEventListener("click", () => liberar(Number(b.dataset.liberar))),
    );
    cont.querySelectorAll("[data-detalhe]").forEach((b) =>
      b.addEventListener("click", () => abrirDetalhe(Number(b.dataset.detalhe))),
    );
  }

  function paradoBadge(d) {
    if (d == null) return "—";
    const cls = d <= 30 ? "ok" : d <= 90 ? "warn" : "bad";
    return `<span class="bat ${cls}" title="${d} dias parado no estoque">${d} d</span>`;
  }

  function linhaHtml(i, ehEstoque, reservadosView) {
    const preco = i.precoVenda != null ? brl.format(i.precoVenda) : "sob consulta";
    const bat = i.saudeBateria != null
      ? `<span class="bat ${i.saudeBateria >= 85 ? "ok" : i.saudeBateria >= 80 ? "warn" : "bad"}">${i.saudeBateria}%</span>`
      : "—";
    let cols = `
      <td class="id">${escapeHtml(i.idCurto)}</td>
      <td>${escapeHtml(i.armazenamento || "—")}</td>
      <td>${escapeHtml(i.cor || "—")}</td>
      <td>${bat}</td>
      <td class="money">${preco}</td>`;
    if (ehEstoque) {
      cols += `
      <td class="money">${i.custo != null ? brl.format(i.custo) : "—"}</td>
      <td class="money">${i.margem != null ? `${brl.format(i.margem)}${i.margemPct != null ? ` (${i.margemPct}%)` : ""}` : "—"}</td>
      <td>${paradoBadge(i.diasEmEstoque)}</td>`;
    }
    const det = escapeHtml(i.detalhe?.texto || "");
    cols += ehEstoque
      ? `<td class="det">${det ? `<span>${det}</span> ` : ""}<button class="linha-acao" data-detalhe="${i.id}">${det ? "editar" : "+ detalhe"}</button></td>`
      : `<td class="det">${det || "—"}</td>`;
    if (ehEstoque) {
      cols += reservadosView
        ? `<td class="reserva-info">${escapeHtml(i.reservado?.vendedor || "")} · <button class="linha-acao" data-liberar="${i.id}">liberar</button></td>`
        : `<td><button class="linha-acao" data-reservar="${i.id}">reservar</button></td>`;
    }
    return `<tr>${cols}</tr>`;
  }

  /* ---------------- Reserva ---------------- */
  const dlg = $("dlgReserva");
  let reservaAlvo = null;

  function abrirReserva(id) {
    const it = estado.itens.find((x) => x.id === id);
    if (!it) return;
    reservaAlvo = id;
    $("dlgResumo").textContent = `${it.modelo} · ${it.estado} · ${it.armazenamento || ""} · ID ${it.idCurto}`;
    $("dlgVendedor").value = "";
    dlg.showModal();
  }

  dlg.addEventListener("close", async () => {
    if (dlg.returnValue !== "ok" || reservaAlvo == null) return;
    const vendedor = $("dlgVendedor").value.trim();
    if (!vendedor) return;
    const r = await fetch("/api/reservar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id: reservaAlvo, vendedor }),
    });
    if (!r.ok) {
      const j = await r.json().catch(() => ({}));
      setStatus(j.erro || "Não foi possível reservar.", true);
    }
    reservaAlvo = null;
    await carregar();
  });

  async function liberar(id) {
    const r = await fetch("/api/desreservar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id }),
    });
    if (!r.ok) {
      const j = await r.json().catch(() => ({}));
      setStatus(j.erro || "Não foi possível liberar.", true);
    }
    await carregar();
  }

  /* ---------------- Detalhes (nota de condição) ---------------- */
  const dlgDet = $("dlgDetalhe");
  let detalheAlvo = null;

  function abrirDetalhe(id) {
    const it = estado.itens.find((x) => x.id === id);
    if (!it) return;
    detalheAlvo = id;
    $("dlgDetResumo").textContent = `${it.modelo} · ${it.estado} · ID ${it.idCurto}`;
    $("dlgDetTexto").value = it.detalhe?.texto || "";
    dlgDet.showModal();
  }

  dlgDet.addEventListener("close", async () => {
    if (dlgDet.returnValue !== "ok" || detalheAlvo == null) return;
    const texto = $("dlgDetTexto").value.trim().slice(0, 280);
    const r = await fetch("/api/detalhe", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id: detalheAlvo, texto }),
    });
    if (!r.ok) {
      const j = await r.json().catch(() => ({}));
      setStatus(j.erro || "Não foi possível salvar o detalhe.", true);
    }
    detalheAlvo = null;
    await carregar();
  });

  /* ---------------- Excel ---------------- */
  $("btnExcel").addEventListener("click", () => {
    const ehEstoque = estado.papel === "estoque";
    const linhas = filtrar();
    const head = ["ID", "Tipo", "Modelo", "Armazenamento", "Cor", "Estado", "Bateria (%)", "Preço"];
    if (ehEstoque) head.push("Custo", "Margem", "Margem (%)", "Dias parado");
    head.push("Detalhes");
    const rows = linhas.map((i) => {
      const base = [i.idCurto, i.tipoProduto, i.modelo, i.armazenamento || "", i.cor || "",
        i.estado, i.saudeBateria ?? "", i.precoVenda ?? ""];
      if (ehEstoque) base.push(i.custo ?? "", i.margem ?? "", i.margemPct ?? "", i.diasEmEstoque ?? "");
      base.push(i.detalhe?.texto || "");
      return base;
    });
    const dia = new Date().toISOString().slice(0, 10);
    window.XlsxMini.baixar(`estoque-${dia}.xlsx`, head, rows);
  });

  /* ---------------- utils ---------------- */
  function setStatus(msg, err) {
    const el = $("statusMsg");
    el.textContent = msg || "";
    el.classList.toggle("err", Boolean(err));
  }
  function atualizarStamp() {
    if (!estado.geradoEm) return;
    const min = Math.max(0, Math.round((Date.now() - Date.parse(estado.geradoEm)) / 60000));
    $("metaStamp").textContent = `Estoque atualizado há ${min} min · ${estado.papel === "estoque" ? "área Estoque" : "área Geral"}`;
    setStatus("");
  }
  function norm(s) {
    return String(s || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
  }
  function escapeHtml(s) {
    return String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  /* Sessão já ativa? tenta direto. */
  fetch("/api/inventory", { headers: { "Cache-Control": "no-store" } }).then((r) => {
    if (r.ok) r.json().then((d) => entrar(d.papel));
  }).catch(() => {});
})();
