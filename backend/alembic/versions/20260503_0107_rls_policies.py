"""rls_policies

Activa Row-Level Security en todas las tablas con tenant_id. Política:
un usuario ve los registros de su tenant + (si su tenant es PRINCIPAL)
los registros de los sub-tenants cuyo parent_tenant_id sea el suyo.

La aplicación setea `app.current_tenant_id` por sesión antes de cada query.
El rol postgres (superuser) BYPASS RLS en local; en prod se usa un rol app_user
sin BYPASSRLS.

Revision ID: 20a1155c2542
Revises: 040714f52a8f
Create Date: 2026-05-03 01:07:49.751459
"""
from typing import Sequence, Union

from alembic import op


revision: str = '20a1155c2542'
down_revision: Union[str, None] = '040714f52a8f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Tablas operativas con tenant_id que requieren RLS
TABLES_WITH_TENANT = [
    "tenants",            # caso especial: filtra por id o parent_tenant_id
    "memberships",
    "contratos",
    "contratos_lotes",    # via contrato.tenant_id
    "unidades_entrega",   # via contrato.tenant_id
    "clientes",
    "productos",
    "listas_precios",
    "precios",            # via lista.tenant_id
    "almacenes",
    "lotes_inventario",
    "movimientos_inventario",
    "mermas",
    "pedidos",
    "lineas_pedido",      # via pedido
    "csds",
    "facturas",
    "lineas_factura",     # via factura
    "pagos",
    "abonos_factura",     # via pago/factura
    "proveedores",
    "ordenes_compra",
    "events_log",
    "mensajes_log",
]

# Política estándar: tenant_id del registro = current_tenant_id
# o el record es de un sub del current_tenant_id (jerarquía)
STANDARD_POLICY_SQL = """
CREATE POLICY tenant_isolation_{table} ON {table}
  FOR ALL
  USING (
    tenant_id = current_setting('app.current_tenant_id', true)::uuid
    OR tenant_id IN (
      SELECT id FROM tenants
      WHERE parent_tenant_id = current_setting('app.current_tenant_id', true)::uuid
    )
  );
"""

TENANTS_POLICY_SQL = """
CREATE POLICY tenant_self_or_children ON tenants
  FOR ALL
  USING (
    id = current_setting('app.current_tenant_id', true)::uuid
    OR parent_tenant_id = current_setting('app.current_tenant_id', true)::uuid
  );
"""

# Tablas con tenant_id directo (la mayoría)
TABLES_DIRECT_TENANT = [
    "memberships", "contratos", "clientes", "productos", "listas_precios",
    "almacenes", "lotes_inventario", "movimientos_inventario", "mermas",
    "pedidos", "csds", "facturas", "pagos", "proveedores", "ordenes_compra",
    "events_log", "mensajes_log",
]


def upgrade() -> None:
    # Habilitar RLS en cada tabla
    for table in TABLES_WITH_TENANT:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")

    # Política especial para tenants (auto-referencia)
    op.execute(TENANTS_POLICY_SQL)

    # Políticas estándar para tablas con tenant_id
    for table in TABLES_DIRECT_TENANT:
        op.execute(STANDARD_POLICY_SQL.format(table=table))

    # Para tablas que dependen de su parent (lineas_pedido, lineas_factura, etc.)
    # se filtran vía join en queries; no necesitan policy directa porque el
    # acceso siempre es vía pedido/factura/etc.
    op.execute("""
    CREATE POLICY lineas_pedido_via_pedido ON lineas_pedido
      FOR ALL
      USING (
        pedido_id IN (
          SELECT id FROM pedidos
          WHERE tenant_id = current_setting('app.current_tenant_id', true)::uuid
            OR tenant_id IN (
              SELECT id FROM tenants
              WHERE parent_tenant_id = current_setting('app.current_tenant_id', true)::uuid
            )
        )
      );
    """)

    op.execute("""
    CREATE POLICY lineas_factura_via_factura ON lineas_factura
      FOR ALL
      USING (
        factura_id IN (
          SELECT id FROM facturas
          WHERE tenant_id = current_setting('app.current_tenant_id', true)::uuid
            OR tenant_id IN (
              SELECT id FROM tenants
              WHERE parent_tenant_id = current_setting('app.current_tenant_id', true)::uuid
            )
        )
      );
    """)

    op.execute("""
    CREATE POLICY abonos_via_pago ON abonos_factura
      FOR ALL
      USING (
        pago_id IN (
          SELECT id FROM pagos
          WHERE tenant_id = current_setting('app.current_tenant_id', true)::uuid
            OR tenant_id IN (
              SELECT id FROM tenants
              WHERE parent_tenant_id = current_setting('app.current_tenant_id', true)::uuid
            )
        )
      );
    """)

    op.execute("""
    CREATE POLICY contratos_lotes_via_contrato ON contratos_lotes
      FOR ALL
      USING (
        contrato_id IN (
          SELECT id FROM contratos
          WHERE tenant_id = current_setting('app.current_tenant_id', true)::uuid
            OR tenant_id IN (
              SELECT id FROM tenants
              WHERE parent_tenant_id = current_setting('app.current_tenant_id', true)::uuid
            )
        )
      );
    """)

    op.execute("""
    CREATE POLICY unidades_via_contrato ON unidades_entrega
      FOR ALL
      USING (
        contrato_id IN (
          SELECT id FROM contratos
          WHERE tenant_id = current_setting('app.current_tenant_id', true)::uuid
            OR tenant_id IN (
              SELECT id FROM tenants
              WHERE parent_tenant_id = current_setting('app.current_tenant_id', true)::uuid
            )
        )
      );
    """)

    op.execute("""
    CREATE POLICY precios_via_lista ON precios
      FOR ALL
      USING (
        lista_id IN (
          SELECT id FROM listas_precios
          WHERE tenant_id = current_setting('app.current_tenant_id', true)::uuid
            OR tenant_id IN (
              SELECT id FROM tenants
              WHERE parent_tenant_id = current_setting('app.current_tenant_id', true)::uuid
            )
        )
      );
    """)


def downgrade() -> None:
    for table in TABLES_WITH_TENANT:
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")
    # drop all policies (Postgres drops them automatically when RLS is disabled
    # if they're referenced only by RLS, but we explicit-drop to be safe)
    op.execute("DROP POLICY IF EXISTS tenant_self_or_children ON tenants;")
    for table in TABLES_DIRECT_TENANT:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_{table} ON {table};")
    op.execute("DROP POLICY IF EXISTS lineas_pedido_via_pedido ON lineas_pedido;")
    op.execute("DROP POLICY IF EXISTS lineas_factura_via_factura ON lineas_factura;")
    op.execute("DROP POLICY IF EXISTS abonos_via_pago ON abonos_factura;")
    op.execute("DROP POLICY IF EXISTS contratos_lotes_via_contrato ON contratos_lotes;")
    op.execute("DROP POLICY IF EXISTS unidades_via_contrato ON unidades_entrega;")
    op.execute("DROP POLICY IF EXISTS precios_via_lista ON precios;")
