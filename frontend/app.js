// Operator dashboard for Cadena de Suministro AI
// All requests go to the same origin (FastAPI mounts /static for these files).

const API = "/api/v1";

const state = {
  tenantId: localStorage.getItem("cdc_tenant_id") || "",
};

// ─── helpers ──────────────────────────────────────────────────────────────

function $(sel) { return document.querySelector(sel); }
function $$(sel) { return document.querySelectorAll(sel); }

async function api(path, opts = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...(opts.headers || {}),
  };
  if (state.tenantId) headers["x-tenant-id"] = state.tenantId;
  const r = await fetch(`${API}${path}`, { ...opts, headers });
  if (!r.ok) {
    const text = await r.text();
    throw new Error(`${r.status}: ${text}`);
  }
  return r.json();
}

function setStatus(msg, kind = "") {
  const el = $("#status");
  el.textContent = msg;
  el.className = "status-pill " + kind;
}

function fmtMoney(v) {
  return new Intl.NumberFormat("es-MX", { style: "currency", currency: "MXN" }).format(v || 0);
}
function fmtNumber(v) {
  return new Intl.NumberFormat("es-MX", { maximumFractionDigits: 2 }).format(v || 0);
}

function todayISO() {
  return new Date().toISOString().slice(0, 10);
}

// ─── tenant bar ──────────────────────────────────────────────────────────

$("#tenant-id").value = state.tenantId;

$("#btn-load").addEventListener("click", async () => {
  state.tenantId = $("#tenant-id").value.trim();
  localStorage.setItem("cdc_tenant_id", state.tenantId);
  await loadAll();
});

async function loadAll() {
  if (!state.tenantId) {
    setStatus("Falta tenant ID", "err");
    return;
  }
  try {
    setStatus("Cargando…");
    await loadDashboard();
    setStatus("OK", "ok");
  } catch (e) {
    setStatus("Error: " + e.message, "err");
  }
}

// ─── tabs ─────────────────────────────────────────────────────────────────

$$(".tab").forEach((b) => {
  b.addEventListener("click", () => {
    $$(".tab").forEach((x) => x.classList.remove("active"));
    $$(".tab-content").forEach((x) => x.classList.remove("active"));
    b.classList.add("active");
    $("#tab-" + b.dataset.tab).classList.add("active");
  });
});

// ─── dashboard ────────────────────────────────────────────────────────────

$("#dash-fecha").value = todayISO();
$("#btn-dash-load").addEventListener("click", loadDashboard);

async function loadDashboard() {
  if (!state.tenantId) return;
  const fecha = $("#dash-fecha").value;
  const [resumen, top, unidades] = await Promise.all([
    api(`/dashboard/resumen-dia?fecha=${fecha}`),
    api(`/dashboard/top-productos?limit=10`),
    api(`/dashboard/top-unidades?limit=10`),
  ]);

  const cards = [
    { label: "Pedidos del día", value: resumen.pedidos_count, sub: `${resumen.lineas_count} líneas` },
    { label: "Total del día", value: fmtMoney(resumen.total_dia) },
    { label: "Requieren review", value: resumen.pedidos_requires_review },
    { label: "Por canal", value: Object.keys(resumen.por_canal).length, sub: Object.entries(resumen.por_canal).map(([k,v]) => `${k}: ${v}`).join(", ") },
  ];
  $("#resumen-cards").innerHTML = cards.map(c => `
    <div class="card">
      <div class="label">${c.label}</div>
      <div class="value">${c.value ?? "-"}</div>
      <div class="sub">${c.sub || ""}</div>
    </div>
  `).join("");

  $("#tbl-top-productos tbody").innerHTML = top.items.map(it => `
    <tr>
      <td><code>${it.sku}</code></td>
      <td>${it.nombre}</td>
      <td>${it.apariciones}</td>
      <td>${fmtNumber(it.cantidad_total)}</td>
      <td>${fmtMoney(it.importe_total)}</td>
    </tr>
  `).join("");

  $("#tbl-top-unidades tbody").innerHTML = unidades.items.map(it => `
    <tr>
      <td><span class="badge">${it.tipo}</span></td>
      <td>${it.nombre}</td>
      <td>${it.pedidos_count}</td>
      <td>${fmtMoney(it.total_revenue)}</td>
    </tr>
  `).join("");
}

// ─── pedidos ──────────────────────────────────────────────────────────────

$("#btn-ped-load").addEventListener("click", loadPedidos);

async function loadPedidos() {
  if (!state.tenantId) return;
  const fecha = $("#ped-fecha").value;
  const estado = $("#ped-estado").value;
  let qs = "limit=50";
  if (fecha) qs += `&fecha=${fecha}`;
  if (estado) qs += `&estado=${estado}`;
  const pedidos = await api(`/pedidos?${qs}`);

  // Cargar info de unidad de cada pedido (paralelo)
  const unidadIds = [...new Set(pedidos.map(p => p.unidad_entrega_id).filter(Boolean))];
  const unidadMap = {};
  // Carga vía dashboard top-unidades es lossy; mejor carga directa
  // (no hay endpoint /unidades-entrega/{id} por defecto, así que usamos el que sí está)
  // Dejamos sin nombre por ahora:
  $("#tbl-pedidos tbody").innerHTML = pedidos.map(p => `
    <tr>
      <td>${p.folio_interno || "-"}</td>
      <td>${p.fecha_pedido}</td>
      <td><code style="font-size:11px">${(p.unidad_entrega_id || "").slice(0,8)}…</code></td>
      <td><span class="badge ${p.estado.toLowerCase()}">${p.estado}</span></td>
      <td>${(p.lineas || []).length}</td>
      <td>${fmtMoney(p.total)}</td>
      <td>${p.requires_review ? '<span class="badge review">REVIEW</span>' : ""}</td>
      <td><button onclick="document.getElementById('cfdi-pedido-id').value='${p.id}'; document.querySelector('[data-tab=cfdi]').click();">CFDI</button></td>
    </tr>
  `).join("");
}

// ─── productos ────────────────────────────────────────────────────────────

$("#btn-prod-load").addEventListener("click", loadProductos);
$("#prod-q").addEventListener("keydown", (e) => { if (e.key === "Enter") loadProductos(); });

async function loadProductos() {
  if (!state.tenantId) return;
  const q = $("#prod-q").value.trim();
  const productos = await api(`/productos?limit=100${q ? `&q=${encodeURIComponent(q)}` : ""}`);
  $("#tbl-productos tbody").innerHTML = productos.map(p => `
    <tr>
      <td><code>${p.sku_interno}</code></td>
      <td>${p.nombre}</td>
      <td>${p.categoria || "-"}</td>
      <td><code>${p.unidad_sat}</code></td>
      <td><code>${p.clave_sat}</code></td>
      <td>${(p.sinonimos || []).map(s => `<span class="badge">${s}</span>`).join(" ")}</td>
    </tr>
  `).join("");
}

// ─── resolver ─────────────────────────────────────────────────────────────

$("#btn-resolver").addEventListener("click", resolverInput);
$("#resolver-input").addEventListener("keydown", (e) => { if (e.key === "Enter") resolverInput(); });

async function resolverInput() {
  if (!state.tenantId) return;
  const alimento = $("#resolver-input").value.trim();
  if (!alimento) return;
  try {
    const r = await api(`/productos/resolve?alimento=${encodeURIComponent(alimento)}`);
    $("#resolver-output").textContent = JSON.stringify(r, null, 2);
  } catch (e) {
    $("#resolver-output").textContent = "Error: " + e.message;
  }
}

// ─── huérfanos (líneas sin producto) ─────────────────────────────────────

$("#btn-huerfanos-load").addEventListener("click", loadHuerfanos);

async function loadHuerfanos() {
  if (!state.tenantId) return;
  const r = await api(`/dashboard/lineas-sin-producto?limit=100`);
  $("#tbl-huerfanos tbody").innerHTML = r.items.map(it => `
    <tr>
      <td>${it.fecha || "-"}</td>
      <td>${it.unidad || "-"}</td>
      <td>${it.texto_original || "-"}</td>
      <td>${fmtNumber(it.cantidad)}</td>
    </tr>
  `).join("");
}

// ─── CFDI preview ─────────────────────────────────────────────────────────

$("#btn-cfdi-preview").addEventListener("click", cfdiPreview);

async function cfdiPreview() {
  if (!state.tenantId) return;
  const id = $("#cfdi-pedido-id").value.trim();
  if (!id) return;
  try {
    const r = await api(`/pedidos/${id}/cfdi-preview`);
    let html = "";
    if (r.errors && r.errors.length) {
      html += `<div class="errors-box"><b>Errores:</b><ul>${r.errors.map(e => `<li><code>${e.field}</code>: ${e.message}</li>`).join("")}</ul></div>`;
    }
    if (r.warnings && r.warnings.length) {
      html += `<div class="warnings-box"><b>Advertencias:</b><ul>${r.warnings.map(w => `<li>${w}</li>`).join("")}</ul></div>`;
    }
    $("#cfdi-validation").innerHTML = html;
    $("#cfdi-output").textContent = r.payload ? JSON.stringify(r.payload, null, 2) : "(sin payload)";
  } catch (e) {
    $("#cfdi-output").textContent = "Error: " + e.message;
  }
}

// ─── boot ────────────────────────────────────────────────────────────────

if (state.tenantId) {
  loadAll();
} else {
  setStatus("Captura tenant ID y dale Cargar", "");
}
