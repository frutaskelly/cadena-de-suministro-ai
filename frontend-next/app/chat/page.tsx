"use client";

import { useCallback, useEffect, useState } from "react";
import { useTenant } from "@/components/TenantProvider";
import ChatSidebar from "@/components/ChatSidebar";
import ChatThread from "@/components/ChatThread";
import ChatComposer from "@/components/ChatComposer";
import { NoTenant } from "@/components/ui";
import { api } from "@/lib/api";
import type {
  ChatConversacion,
  ChatConversacionDetail,
  ChatMensaje,
  ChatAttachment,
} from "@/lib/types";

export default function ChatPage() {
  const { tenant } = useTenant();
  const [conversaciones, setConversaciones] = useState<ChatConversacion[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [mensajes, setMensajes] = useState<ChatMensaje[]>([]);
  const [loadingList, setLoadingList] = useState(false);
  const [loadingThread, setLoadingThread] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadConversaciones = useCallback(async () => {
    if (!tenant) return;
    setLoadingList(true);
    try {
      const list = await api<ChatConversacion[]>(`/api/v1/chat/conversaciones`);
      setConversaciones(list);
      if (!activeId && list.length > 0) {
        setActiveId(list[0].id);
      }
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoadingList(false);
    }
  }, [tenant, activeId]);

  const loadConversacion = useCallback(async (id: string) => {
    setLoadingThread(true);
    setError(null);
    try {
      const detail = await api<ChatConversacionDetail>(
        `/api/v1/chat/conversaciones/${id}`
      );
      setMensajes(detail.mensajes);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoadingThread(false);
    }
  }, []);

  useEffect(() => {
    loadConversaciones();
  }, [tenant, loadConversaciones]);

  useEffect(() => {
    if (activeId) {
      loadConversacion(activeId);
    } else {
      setMensajes([]);
    }
  }, [activeId, loadConversacion]);

  async function handleNew() {
    if (!tenant) return;
    try {
      const created = await api<ChatConversacion>(
        `/api/v1/chat/conversaciones`,
        { method: "POST", body: { titulo: "Nueva conversación" } }
      );
      setConversaciones((prev) => [created, ...prev]);
      setActiveId(created.id);
      setMensajes([]);
    } catch (e) {
      alert((e as Error).message);
    }
  }

  async function handleDelete(id: string) {
    try {
      await api(`/api/v1/chat/conversaciones/${id}`, { method: "DELETE" });
      setConversaciones((prev) => prev.filter((c) => c.id !== id));
      if (activeId === id) {
        setActiveId(null);
        setMensajes([]);
      }
    } catch (e) {
      alert((e as Error).message);
    }
  }

  async function handleSend(texto: string, adjuntos: ChatAttachment[]) {
    let convId = activeId;
    // si no hay conv activa, crear una
    if (!convId) {
      const created = await api<ChatConversacion>(
        `/api/v1/chat/conversaciones`,
        { method: "POST", body: {} }
      );
      setConversaciones((prev) => [created, ...prev]);
      setActiveId(created.id);
      convId = created.id;
    }

    // Optimistic: agregar el mensaje user al thread
    const optimisticUser: ChatMensaje = {
      id: `tmp-${Date.now()}`,
      conversacion_id: convId,
      role: "user",
      contenido: texto,
      adjuntos,
      ai_metadata: {},
      accion: null,
      accion_payload: null,
      accion_resultado: null,
      created_at: new Date().toISOString(),
    };
    setMensajes((prev) => [...prev, optimisticUser]);
    setSending(true);
    setError(null);

    try {
      const asst = await api<ChatMensaje>(
        `/api/v1/chat/conversaciones/${convId}/mensajes`,
        {
          method: "POST",
          body: { contenido: texto, adjuntos },
        }
      );
      // Reemplazar optimistic + agregar respuesta — recargamos del server
      // para tener el mensaje user persistido con su id real
      const detail = await api<ChatConversacionDetail>(
        `/api/v1/chat/conversaciones/${convId}`
      );
      setMensajes(detail.mensajes);
      // refrescar lista para ver titulo nuevo / ultima_actividad
      loadConversaciones();
      void asst;
    } catch (e) {
      setError((e as Error).message);
      // revertir optimistic
      setMensajes((prev) => prev.filter((m) => m.id !== optimisticUser.id));
    } finally {
      setSending(false);
    }
  }

  if (!tenant) {
    return (
      <div className="flex items-center justify-center h-screen">
        <NoTenant />
      </div>
    );
  }

  const activeConv = conversaciones.find((c) => c.id === activeId);

  return (
    <div className="flex h-screen overflow-hidden">
      <ChatSidebar
        conversaciones={conversaciones}
        activeId={activeId}
        onSelect={setActiveId}
        onNew={handleNew}
        onDelete={handleDelete}
        loading={loadingList}
      />

      <div className="flex-1 flex flex-col min-w-0">
        <header
          className="flex items-center justify-between px-7 h-14 border-b backdrop-blur-md"
          style={{
            borderColor: "var(--border-subtle)",
            background: "rgba(255,255,255,0.78)",
          }}
        >
          <div className="text-title truncate">
            {activeConv?.titulo || "Chat"}
          </div>
          <div className="flex items-center gap-2">
            {activeConv && (
              <span className="text-caption">
                {activeConv.mensajes_count} mensajes ·{" "}
                {activeConv.tokens_in + activeConv.tokens_out} tokens
              </span>
            )}
          </div>
        </header>

        {error && (
          <div
            className="px-7 py-2 text-[12px]"
            style={{
              background: "rgba(220, 0, 0, 0.05)",
              color: "#a93226",
              borderBottom: "1px solid var(--border-subtle)",
            }}
          >
            {error}
          </div>
        )}

        <ChatThread mensajes={mensajes} loading={sending} />

        <ChatComposer
          onSend={handleSend}
          disabled={loadingThread}
        />
      </div>
    </div>
  );
}
