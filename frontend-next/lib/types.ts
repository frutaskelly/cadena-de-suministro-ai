/** Tipos TypeScript matching backend schemas */

export type Pedido = {
  id: string;
  tenant_id: string;
  folio_interno: string | null;
  cliente_facturacion_id: string;
  unidad_entrega_id: string | null;
  fecha_pedido: string;
  fecha_entrega: string | null;
  estado: string;
  canal: string;
  subtotal: string;
  iva: string;
  total: string;
  requires_review: boolean;
  notas: string | null;
  created_at: string;
  updated_at: string;
};

export type Producto = {
  id: string;
  tenant_id: string;
  sku_interno: string;
  nombre: string;
  nombre_normalizado: string | null;
  categoria: string | null;
  categoria_extendida: string | null;
  es_catalogado: boolean;
  perecedero: boolean;
  cold_chain: boolean;
  requiere_lote: boolean;
  requiere_caducidad: boolean;
  vida_util_dias: number | null;
  clave_sat: string;
  unidad_sat: string;
  iva_tasa: string;
  presentaciones: Record<string, number>;
  presentacion_default: string;
  sinonimos: string[];
  activo: boolean;
  costo_promedio: string;
};

export type Remision = {
  id: string;
  tenant_id: string;
  folio: string;
  pedido_id: string | null;
  cliente_id: string;
  unidad_entrega_id: string | null;
  almacen_origen_id: string | null;
  fecha_generada: string;
  fecha_entrega: string | null;
  fecha_facturada: string | null;
  estado: string;
  factura_id: string | null;
  subtotal: string | null;
  iva_total: string | null;
  total: string | null;
  notas: string | null;
  created_at: string;
  updated_at: string;
  lineas: LineaRemision[];
};

export type LineaRemision = {
  id: string;
  remision_id: string;
  producto_id: string;
  linea_pedido_id: string | null;
  lote_inventario_id: string | null;
  cantidad_solicitada: string;
  cantidad_entregada: string;
  cantidad_facturada: string | null;
  presentacion: string | null;
  precio_unitario: string;
  importe: string;
  motivo_ajuste: string | null;
  created_at: string;
};

export type OrdenCompra = {
  id: string;
  tenant_id: string;
  folio: string | null;
  proveedor_id: string;
  pedido_origen_id: string | null;
  almacen_destino_id: string | null;
  fecha: string;
  fecha_entrega_esperada: string | null;
  fecha_recibida: string | null;
  estado: string;
  subtotal: string | null;
  iva_total: string | null;
  total_estimado: string | null;
  total_recibido: string | null;
  notas: string | null;
  created_at: string;
  updated_at: string;
  lineas: LineaOrdenCompra[];
};

export type LineaOrdenCompra = {
  id: string;
  orden_compra_id: string;
  producto_id: string;
  cantidad_solicitada: string;
  cantidad_recibida: string;
  presentacion: string | null;
  precio_unitario: string;
  importe: string;
  notas: string | null;
};

export type Conversion = {
  id: string;
  tenant_id: string;
  producto_catalogado_id: string;
  producto_no_catalogado_id: string;
  factor: string;
  merma_pct: string;
  precio_no_cat: string | null;
  mezcla_grupo_id: string | null;
  mezcla_proporcion: string | null;
  prioridad: number;
  requiere_aprobacion: boolean;
  activo: boolean;
  notas: string | null;
};

export type InventarioEstado = {
  producto_id: string;
  producto_nombre: string;
  almacen_id: string;
  cantidad_fisica: string;
  cantidad_remision: string;
  cantidad_facturada_acumulada: string;
  total_disponible_efectivo: string;
};

export type DashboardResumen = {
  fecha: string;
  pedidos_count: number;
  pedidos_requires_review: number;
  lineas_count: number;
  total_dia: number;
  por_estado: Record<string, number>;
  por_canal: Record<string, number>;
};

export type TopProductoItem = {
  producto_id: string;
  sku: string;
  nombre: string;
  cantidad_total: number;
  importe_total: number;
  apariciones: number;
};
export type TopProductos = {
  desde: string;
  hasta: string;
  items: TopProductoItem[];
};

export type TopUnidadItem = {
  unidad_id: string;
  nombre: string;
  tipo: string;
  pedidos_count: number;
  total_revenue: number;
};
export type TopUnidades = {
  desde: string;
  hasta: string;
  items: TopUnidadItem[];
};
