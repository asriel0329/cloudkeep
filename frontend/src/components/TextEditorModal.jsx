import { useEffect, useState } from "react";
import client from "../api/client";
import { uploadFile } from "../api/files";

const TEXT_EXTENSIONS = [".txt", ".md", ".json", ".csv", ".log", ".yml", ".yaml", ".xml"];

export function isTextEditable(file) {
  if (file.mime_type?.startsWith("text/")) return true;
  return TEXT_EXTENSIONS.some((ext) => file.name.toLowerCase().endsWith(ext));
}

export default function TextEditorModal({ file, folderId, onClose, onSaved }) {
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [dirty, setDirty] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        // 用 GET 抓內容，跟真正的「下載檔案」不同——這裡拿到的是
        // 純文字內容給 textarea 顯示，不會觸發瀏覽器的下載對話框。
        const res = await client.get(`/files/${file.id}/download/`, {
          responseType: "text",
        });
        if (!cancelled) setContent(res.data);
      } catch (err) {
        if (!cancelled) setError("無法載入檔案內容");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [file.id]);

  async function handleSave() {
    setSaving(true);
    setError(null);
    try {
      // 包成一個跟原檔名一樣的 File 物件，上傳 API 會自動辨識出
      // 「這是同資料夾、同檔名」，走 P5-5 的版本控制邏輯，
      // 產生新版本，不會被當成一個獨立的新檔案。
      const blob = new Blob([content], { type: file.mime_type || "text/plain" });
      const editedFile = new window.File([blob], file.name, {
        type: file.mime_type || "text/plain",
      });

      await uploadFile(editedFile, folderId);
      setDirty(false);
      onSaved?.();
    } catch (err) {
      setError(err.response?.data?.detail || "存檔失敗");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.4)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 100,
      }}
    >
      <div
        style={{
          background: "#fff",
          borderRadius: "8px",
          width: "min(800px, 90vw)",
          height: "min(600px, 80vh)",
          display: "flex",
          flexDirection: "column",
          padding: "1rem",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
          <strong>{file.name}{dirty ? " *" : ""}</strong>
          <div style={{ display: "flex", gap: "0.5rem" }}>
            <button onClick={handleSave} disabled={saving || loading}>
              {saving ? "儲存中..." : "儲存"}
            </button>
            <button onClick={onClose}>關閉</button>
          </div>
        </div>

        {error && <p style={{ color: "red", margin: "0 0 0.5rem" }}>{error}</p>}

        {loading ? (
          <p>載入中...</p>
        ) : (
          <textarea
            value={content}
            onChange={(e) => {
              setContent(e.target.value);
              setDirty(true);
            }}
            style={{
              flex: 1,
              fontFamily: "monospace",
              fontSize: "0.9rem",
              padding: "0.5rem",
              resize: "none",
            }}
          />
        )}
      </div>
    </div>
  );
}