// AUDIT H11: loading.tsx global para route segments async.
// Suspense boundary automatico mientras se carga cada page.

export default function GlobalLoading() {
  return (
    <div className="px-7 py-7 max-w-[1400px] mx-auto">
      <div className="card p-12 text-center">
        <div className="inline-block">
          <span
            className="w-2 h-2 rounded-full bg-black inline-block mr-1 animate-pulse"
            style={{ animationDelay: "0s" }}
          />
          <span
            className="w-2 h-2 rounded-full bg-black inline-block mr-1 animate-pulse"
            style={{ animationDelay: "0.15s" }}
          />
          <span
            className="w-2 h-2 rounded-full bg-black inline-block animate-pulse"
            style={{ animationDelay: "0.3s" }}
          />
        </div>
        <div className="text-caption mt-3">Cargando…</div>
      </div>
    </div>
  );
}
