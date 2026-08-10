import { useEffect, useState } from "react";
import {
  createPermission,
  listPermissions,
  revokePermission,
} from "../api/permissions";

export default function PermissionModal({
  folder,
  onClose,
}) {
  const [permissions, setPermissions] = useState([]);
  const [userId, setUserId] = useState("");
  const [level, setLevel] = useState("read");

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [busyId, setBusyId] = useState(null);
  const [error, setError] = useState(null);

  async function loadPermissions() {
    setLoading(true);
    setError(null);

    try {
      const data = await listPermissions(folder.id);
      setPermissions(data);
    } catch (err) {
      setError(
        err.response?.data?.detail || "載入權限失敗"
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadPermissions();
  }, [folder.id]);

  async function handleCreate(e) {
    e.preventDefault();

    if (!userId.trim()) {
      setError("請輸入使用者 ID");
      return;
    }

    const numericUserId = Number(userId);

    if (!Number.isInteger(numericUserId) || numericUserId <= 0) {
      setError("使用者 ID 必須是正整數");
      return;
    }

    setSaving(true);
    setError(null);

    try {
      await createPermission(folder.id, numericUserId, level);

      setUserId("");
      setLevel("read");

      await loadPermissions();
    } catch (err) {
      const message =
        err.response?.data?.detail ||
        err.response?.data?.non_field_errors?.[0] ||
        err.response?.data?.user?.[0] ||
        "新增權限失敗";

      setError(message);
    } finally {
      setSaving(false);
    }
  }

  async function handleRevoke(permission) {
    if (
      !window.confirm(
        `確定要撤銷使用者 ${permission.user} 的權限嗎？`
      )
    ) {
      return;
    }

    setBusyId(permission.id);
    setError(null);

    try {
      await revokePermission(permission.id);

      setPermissions((prev) =>
        prev.filter((p) => p.id !== permission.id)
      );
    } catch (err) {
      setError(
        err.response?.data?.detail || "撤銷權限失敗"
      );
    } finally {
      setBusyId(null);
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
          width: "min(600px, calc(100vw - 2rem))",
          maxHeight: "80vh",
          overflowY: "auto",
          background: "#fff",
          borderRadius: "10px",
          padding: "1.5rem",
          boxShadow: "0 10px 40px rgba(0,0,0,0.2)",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <h2 style={{ marginTop: 0 }}>
            「{folder.name}」權限管理
          </h2>

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

        {error && (
          <p style={{ color: "red" }}>
            {error}
          </p>
        )}

        <h3>目前授權</h3>

        {loading ? (
          <p>載入權限中...</p>
        ) : permissions.length === 0 ? (
          <p style={{ color: "#888" }}>
            目前沒有其他使用者被授權。
          </p>
        ) : (
          <ul
            style={{
              listStyle: "none",
              padding: 0,
            }}
          >
            {permissions.map((permission) => (
              <li
                key={permission.id}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  padding: "0.75rem",
                  border: "1px solid #eee",
                  borderRadius: "6px",
                  marginBottom: "0.5rem",
                }}
              >
                <div>
                  <strong>
                    使用者 #{permission.user}
                  </strong>

                  <div
                    style={{
                      color: "#666",
                      fontSize: "0.9rem",
                    }}
                  >
                    權限：
                    {permission.level === "write"
                      ? "可讀寫"
                      : "唯讀"}
                  </div>
                </div>

                <button
                  onClick={() => handleRevoke(permission)}
                  disabled={busyId === permission.id}
                >
                  {busyId === permission.id
                    ? "處理中..."
                    : "撤銷"}
                </button>
              </li>
            ))}
          </ul>
        )}

        <hr />

        <h3>新增授權</h3>

        <form onSubmit={handleCreate}>
          <div style={{ marginBottom: "0.75rem" }}>
            <label
              style={{
                display: "block",
                marginBottom: "0.3rem",
              }}
            >
              使用者 ID
            </label>

            <input
              type="number"
              min="1"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              placeholder="例如 3"
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
                display: "block",
                marginBottom: "0.3rem",
              }}
            >
              權限
            </label>

            <select
              value={level}
              onChange={(e) => setLevel(e.target.value)}
              style={{
                width: "100%",
                padding: "0.6rem",
              }}
            >
              <option value="read">唯讀</option>
              <option value="write">可讀寫</option>
            </select>
          </div>

          <div
            style={{
              display: "flex",
              justifyContent: "flex-end",
              gap: "0.5rem",
            }}
          >
            <button
              type="button"
              onClick={onClose}
              disabled={saving}
            >
              關閉
            </button>

            <button type="submit" disabled={saving}>
              {saving ? "新增中..." : "新增授權"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}