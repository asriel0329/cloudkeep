import { useState } from "react";
import { chunkedUpload, resumeUpload, shouldUseChunkedUpload } from "../api/chunkedUpload";
import { uploadFile } from "../api/files";

export default function UploadProgressModal({ file, folderId, onClose, onUploaded }) {
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);
  const [failedSessionId, setFailedSessionId] = useState(null);
  const [uploading, setUploading] = useState(true);

  async function runUpload(resumeSessionId) {
    setUploading(true);
    setError(null);
    try {
      let result;
      if (resumeSessionId) {
        result = await resumeUpload(file, resumeSessionId, setProgress);
      } else if (shouldUseChunkedUpload(file)) {
        result = await chunkedUpload(file, folderId, setProgress);
      } else {
        // 小檔案：直接用原本簡單的上傳方式，onUploadProgress 是 axios 原生支援的進度回呼
        result = await uploadFile(file, folderId, (evt) => {
          setProgress(Math.round((evt.loaded / evt.total) * 100));
        });
      }
      onUploaded?.(result);
    } catch (err) {
      setError(err.response?.data?.detail || "上傳失敗，網路可能中斷了");
      if (err.sessionId) {
        setFailedSessionId(err.sessionId);
      }
    } finally {
      setUploading(false);
    }
  }

  useState(() => {
    runUpload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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
      <div style={{ background: "#fff", borderRadius: "8px", padding: "1.5rem", width: "min(420px, 90vw)" }}>
        <p style={{ marginTop: 0 }}>
          {uploading ? "上傳中" : error ? "上傳中斷" : "完成"}：{file.name}
        </p>

        <div style={{ background: "#eee", borderRadius: "4px", height: "10px", overflow: "hidden", marginBottom: "0.75rem" }}>
          <div style={{ width: `${progress}%`, background: error ? "#e53e3e" : "#3182ce", height: "100%" }} />
        </div>

        <p style={{ fontSize: "0.85rem", color: "#666" }}>{progress}%</p>

        {error && <p style={{ color: "red", fontSize: "0.9rem" }}>{error}</p>}

        <div style={{ display: "flex", gap: "0.5rem", justifyContent: "flex-end" }}>
          {error && failedSessionId && (
            <button onClick={() => runUpload(failedSessionId)}>接著傳</button>
          )}
          <button onClick={onClose}>{uploading ? "背景執行" : "關閉"}</button>
        </div>
      </div>
    </div>
  );
}