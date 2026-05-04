"use client";

import { useRef, useState, KeyboardEvent } from "react";
import { ChatAttachment } from "@/lib/types";

const MAX_FILE_SIZE_MB = 10;

export default function ChatComposer({
  onSend,
  disabled,
}: {
  onSend: (texto: string, adjuntos: ChatAttachment[]) => Promise<void> | void;
  disabled?: boolean;
}) {
  const [texto, setTexto] = useState("");
  const [files, setFiles] = useState<ChatAttachment[]>([]);
  const [sending, setSending] = useState(false);
  const inputRef = useRef<HTMLInputElement | null>(null);

  async function handleFiles(fileList: FileList | null) {
    if (!fileList) return;
    const next: ChatAttachment[] = [];
    for (const f of Array.from(fileList)) {
      if (f.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
        alert(`${f.name} excede ${MAX_FILE_SIZE_MB} MB. Salteado.`);
        continue;
      }
      const buf = await f.arrayBuffer();
      const bytes = new Uint8Array(buf);
      // base64 encode without breaking on large files
      let bin = "";
      for (let i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]);
      const data_b64 = btoa(bin);
      next.push({
        nombre: f.name,
        mime: f.type || "application/octet-stream",
        size: f.size,
        data_b64,
      });
    }
    setFiles((prev) => [...prev, ...next]);
    if (inputRef.current) inputRef.current.value = "";
  }

  function removeFile(idx: number) {
    setFiles((prev) => prev.filter((_, i) => i !== idx));
  }

  async function handleSend() {
    if (sending || disabled) return;
    if (!texto.trim() && files.length === 0) return;
    setSending(true);
    try {
      await onSend(texto, files);
      setTexto("");
      setFiles([]);
    } finally {
      setSending(false);
    }
  }

  function handleKey(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  const canSend = !sending && !disabled && (texto.trim() || files.length > 0);

  return (
    <div
      className="border-t px-7 py-4 bg-[var(--background)]"
      style={{ borderColor: "var(--border-subtle)" }}
    >
      <div className="max-w-3xl mx-auto">
        {/* Adjuntos pendientes de enviar */}
        {files.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-3">
            {files.map((f, i) => (
              <div
                key={i}
                className="card-soft px-3 py-2 inline-flex items-center gap-2"
              >
                <span className="text-[12px] font-medium truncate max-w-[200px]">
                  {f.nombre}
                </span>
                <span
                  className="text-[10.5px]"
                  style={{ color: "var(--text-tertiary)" }}
                >
                  {(f.size / 1024).toFixed(1)} KB
                </span>
                <button
                  onClick={() => removeFile(i)}
                  className="ml-1 text-[14px] leading-none"
                  style={{
                    color: "var(--text-tertiary)",
                    background: "transparent",
                    border: "none",
                    cursor: "pointer",
                  }}
                  aria-label="Quitar archivo"
                  title="Quitar"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        )}

        <div
          className="flex items-end gap-2 card p-2"
          style={{ borderRadius: 18 }}
        >
          <input
            ref={inputRef}
            type="file"
            multiple
            accept="image/*,application/pdf,.xlsx,.xls,.csv,.txt"
            onChange={(e) => handleFiles(e.target.files)}
            style={{ display: "none" }}
            id="chat-file-input"
          />
          <label
            htmlFor="chat-file-input"
            className="flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center cursor-pointer transition-all"
            style={{
              background: "var(--surface)",
              color: "var(--text-secondary)",
            }}
            title="Adjuntar archivo (Excel, PDF, foto)"
          >
            <span style={{ fontSize: 18, lineHeight: 1 }}>+</span>
          </label>

          <textarea
            value={texto}
            onChange={(e) => setTexto(e.target.value)}
            onKeyDown={handleKey}
            rows={1}
            placeholder={
              disabled
                ? "Selecciona o crea una conversación…"
                : "Escribe aquí — o adjunta un Excel, foto, PDF…"
            }
            className="flex-1 resize-none outline-none px-2 py-2 text-[14px] bg-transparent"
            style={{
              fontFamily: "inherit",
              maxHeight: 160,
              lineHeight: 1.5,
            }}
            disabled={disabled || sending}
            aria-label="Mensaje"
          />

          <button
            onClick={handleSend}
            disabled={!canSend}
            className="btn-primary flex-shrink-0"
            style={{ borderRadius: 12, padding: "8px 14px" }}
          >
            {sending ? "Enviando…" : "Enviar"}
          </button>
        </div>

        <div
          className="text-[10.5px] mt-2 text-center"
          style={{ color: "var(--text-tertiary)" }}
        >
          Enter para enviar · Shift+Enter para salto de línea · Max 10 MB por archivo
        </div>
      </div>
    </div>
  );
}
