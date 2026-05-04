"use client";

// AUDIT H11: error.tsx para capturar crashes en cualquier route.
// Sin esto, un error de renderizado deja la UI en blanco.

import { useEffect } from "react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // En produccion: enviar a Sentry.
    // eslint-disable-next-line no-console
    console.error("[GlobalError]", error);
  }, [error]);

  return (
    <div className="px-7 py-7 max-w-[1400px] mx-auto">
      <div className="card p-10 text-center">
        <div className="text-headline mb-2">Algo no salió bien</div>
        <div className="text-caption mb-6">
          Ocurrió un error al cargar esta vista. Si persiste, recarga o cambia
          de tenant.
        </div>
        {error.message && (
          <div
            className="text-[12px] font-mono mb-6 p-3 card-soft text-left max-w-2xl mx-auto break-all"
            style={{ color: "var(--text-secondary)" }}
          >
            {error.message}
          </div>
        )}
        <div className="flex gap-2 justify-center">
          <button className="btn-primary" onClick={reset}>
            Reintentar
          </button>
          <button
            className="btn-outline"
            onClick={() => window.location.reload()}
          >
            Recargar página
          </button>
        </div>
      </div>
    </div>
  );
}
