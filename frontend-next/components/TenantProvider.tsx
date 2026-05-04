"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  ReactNode,
} from "react";
import {
  getTenantId as readTenantId,
  setTenantId as writeTenantId,
  clearTenantId as removeTenantId,
} from "@/lib/api";

type TenantState = {
  tenant: string | null;
  setTenant: (id: string) => void;
  clear: () => void;
  ready: boolean;
};

const Ctx = createContext<TenantState>({
  tenant: null,
  setTenant: () => {},
  clear: () => {},
  ready: false,
});

const STORAGE_EVENT = "tenant-changed";

export function TenantProvider({ children }: { children: ReactNode }) {
  const [tenant, setTenantState] = useState<string | null>(null);
  const [ready, setReady] = useState(false);

  // Initial read once + sync via custom event (fixes AUDIT C5: no polling 1s)
  useEffect(() => {
    setTenantState(readTenantId());
    setReady(true);

    const onChange = () => setTenantState(readTenantId());
    window.addEventListener(STORAGE_EVENT, onChange);
    // cross-tab sync
    window.addEventListener("storage", onChange);
    return () => {
      window.removeEventListener(STORAGE_EVENT, onChange);
      window.removeEventListener("storage", onChange);
    };
  }, []);

  const setTenant = useCallback((id: string) => {
    writeTenantId(id);
    setTenantState(id);
    window.dispatchEvent(new Event(STORAGE_EVENT));
  }, []);

  const clear = useCallback(() => {
    removeTenantId();
    setTenantState(null);
    window.dispatchEvent(new Event(STORAGE_EVENT));
  }, []);

  return (
    <Ctx.Provider value={{ tenant, setTenant, clear, ready }}>
      {children}
    </Ctx.Provider>
  );
}

export function useTenant(): TenantState {
  return useContext(Ctx);
}
