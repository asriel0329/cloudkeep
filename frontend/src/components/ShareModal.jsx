import { useState } from "react";
import { createShare } from "../api/shares";

export default function ShareModal({
  file = null,
  folder = null,
  onClose,
}) {
  const [permissionLevel, setPermissionLevel] = useState("read");
  const [password, setPassword] = useState("");
  const [hasExpiry, setHasExpiry] = useState(false);
  const [expiresAt, setExpiresAt] = useState("");

  const [creating, setCreating] = useState(false);
  const [error, setError] = useState(null);
  const [share, setShare] = useState(null);
  const [copied, setCopied] = useState(false);

  const targetName = file?.name || folder?.name || "項目";

  async function handleCreate() {
    setCreating(true);
    setError(null);

    try {
      const data = await createShare({
        file: file?.id ?? null,
        folder: folder?.id ?? null,
        permission_level: permissionLevel,
        password,
        expires_at: hasExpiry && expiresAt ? new Date(expiresAt).toISOString() : null,
      });

      setShare(data);
    } catch (err) {
      const message =
        err.response?.data?.detail ||
        err.response?.data?.non_field_errors?.[0] ||
        err.response?.data?.file?.[0] ||
        err.response?.data?.folder?.[0] ||
        "建立分享連結失敗";

      setError(message);
    } finally {
      setCreating(false);
    }
  }

  const shareUrl = share
    ? `${window.location.origin}/share/${share.token}`
    : "";

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(shareUrl);
      setCopied(true);

      setTimeout(() => {
        setCopied(false);
      }, 2000);
    } catch {
      setError("複製連結失敗，請手動複製。");
    }
  }

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0, 0, 0, 0.45)",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        zIndex: 1000,
      }}
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) {
          onClose();
        }
      }}
    >
      <div
        style={{
          width: "min(500px, calc(100vw - 2rem))",
          background: "#fff",
          borderRadius: "10px",
          padding: "1.5rem",
          boxShadow: "0 10px 40px rgba(0,0,0,0.2)",
        }}
      >
        {!share ? (
          <>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: "1.5rem",
              }}
            >
              <h2 style={{ margin: 0 }}>分享「{targetName}」</h2>

              <button
                onClick={onClose}
                style={{
                  border: "none",
                  background: "none",
                  fontSize: "1.3rem",
                  cursor: "pointer",
                }}
              >
                ×
              </button>
            </div>

            <div style={{ marginBottom: "1rem" }}>
              <label
                style={{
                  display: "block",
                  marginBottom: "0.5rem",
                  fontWeight: "bold",
                }}
              >
                權限
              </label>

              <select
                value={permissionLevel}
                onChange={(e) => setPermissionLevel(e.target.value)}
                style={{
                  width: "100%",
                  padding: "0.6rem",
                  boxSizing: "border-box",
                }}
              >
                <option value="read">唯讀</option>
                <option value="write">可讀寫</option>
              </select>
            </div>

            <div style={{ marginBottom: "1rem" }}>
              <label
                style={{
                  display: "block",
                  marginBottom: "0.5rem",
                  fontWeight: "bold",
                }}
              >
                分享密碼
              </label>

              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="留空代表不設定密碼"
                style={{
                  width: "100%",
                  padding: "0.6rem",
                  boxSizing: "border-box",
                }}
              />
            </div>

            <div style={{ marginBottom: "1rem" }}>
              <label
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "0.5rem",
                  marginBottom: "0.5rem",
                  fontWeight: "bold",
                }}
              >
                <input
                  type="checkbox"
                  checked={hasExpiry}
                  onChange={(e) => setHasExpiry(e.target.checked)}
                />
                設定到期時間
              </label>

              {hasExpiry && (
                <input
                  type="datetime-local"
                  value={expiresAt}
                  onChange={(e) => setExpiresAt(e.target.value)}
                  min={new Date().toISOString().slice(0, 16)}
                  style={{
                    width: "100%",
                    padding: "0.6rem",
                    boxSizing: "border-box",
                  }}
                />
              )}
            </div>

            {error && (
              <p style={{ color: "red", marginBottom: "1rem" }}>
                {error}
              </p>
            )}

            <div
              style={{
                display: "flex",
                justifyContent: "flex-end",
                gap: "0.5rem",
              }}
            >
              <button onClick={onClose} disabled={creating}>
                取消
              </button>

              <button onClick={handleCreate} disabled={creating}>
                {creating ? "建立中..." : "建立分享連結"}
              </button>
            </div>
          </>
        ) : (
          <>
            <h2 style={{ marginTop: 0 }}>分享連結已建立</h2>

            <p>
              「{targetName}」已成功建立分享連結。
            </p>

            <div
              style={{
                display: "flex",
                gap: "0.5rem",
                marginBottom: "1rem",
              }}
            >
              <input
                value={shareUrl}
                readOnly
                style={{
                  flex: 1,
                  padding: "0.6rem",
                  minWidth: 0,
                }}
                onFocus={(e) => e.target.select()}
              />

              <button onClick={handleCopy}>
                {copied ? "已複製" : "複製"}
              </button>
            </div>

            <div
              style={{
                background: "#f7f7f7",
                padding: "1rem",
                borderRadius: "6px",
                marginBottom: "1rem",
              }}
            >
              <div>
                權限：
                {share.permission_level === "write"
                  ? "可讀寫"
                  : "唯讀"}
              </div>

              <div>
                密碼：
                {password ? "已設定" : "未設定"}
              </div>

              <div>
                到期：
                {share.expires_at
                  ? new Date(share.expires_at).toLocaleString()
                  : "永不過期"}
              </div>
            </div>

            <div style={{ textAlign: "right" }}>
              <button onClick={onClose}>完成</button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}