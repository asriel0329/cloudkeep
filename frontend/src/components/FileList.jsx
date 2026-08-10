import { useState } from "react";

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  if (bytes < 1024 * 1024 * 1024) {
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
}

export default function FileList({
  files,
  onDownload,
  onDelete,
  onShare,
}) {
  const [busyId, setBusyId] = useState(null);

  async function handleDownload(file) {
    setBusyId(file.id);

    try {
      await onDownload(file);
    } finally {
      setBusyId(null);
    }
  }

  async function handleDelete(file) {
    if (!window.confirm(`確定要刪除「${file.name}」嗎？`)) {
      return;
    }

    setBusyId(file.id);

    try {
      await onDelete(file);
    } finally {
      setBusyId(null);
    }
  }

  if (files.length === 0) {
    return (
      <p style={{ color: "#888" }}>
        這裡還沒有任何檔案。
      </p>
    );
  }

  return (
    <ul style={{ listStyle: "none", padding: 0 }}>
      {files.map((f) => (
        <li
          key={f.id}
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            padding: "0.5rem",
            borderBottom: "1px solid #eee",
          }}
        >
          <div>
            📄 {f.name}{" "}
            <span
              style={{
                color: "#888",
                fontSize: "0.85rem",
              }}
            >
              ({formatSize(f.size)})
            </span>
          </div>

          <div
            style={{
              display: "flex",
              gap: "0.4rem",
            }}
          >
            <button
              onClick={() => handleDownload(f)}
              disabled={busyId === f.id}
            >
              下載
            </button>

            <button
              onClick={() => onShare?.(f)}
              disabled={busyId === f.id}
            >
              分享
            </button>

            <button
              onClick={() => handleDelete(f)}
              disabled={busyId === f.id}
            >
              刪除
            </button>
          </div>
        </li>
      ))}
    </ul>
  );
}