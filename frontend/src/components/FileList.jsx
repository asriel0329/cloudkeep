import { useRef, useState } from "react";

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

// 只有圖片/影片這類有意義產生縮圖的檔案，才需要嘗試載入縮圖，
// 文字檔、壓縮檔這種去打縮圖 API 只會得到 404，不如直接跳過。
function isPreviewable(mimeType) {
  return mimeType?.startsWith("image/") || mimeType?.startsWith("video/");
}

export default function FileList({
  files,
  onDownload,
  onDelete,
  onShare,
}) {
  const [busyId, setBusyId] = useState(null);

  // 每個檔案 hover 時的縮圖狀態各自獨立管理：
  // 有沒有在 hover、縮圖網址、有沒有讀取失敗（例如縮圖還沒產生完）
  const [hoveredId, setHoveredId] = useState(null);
  const [thumbnails, setThumbnails] = useState({}); // { [fileId]: "blob:..." 或 "error" }
  const hoverTimer = useRef(null);

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

  function handleMouseEnter(file) {
    if (!isPreviewable(file.mime_type)) return;

    // 稍微延遲一下才載入，避免滑鼠只是「路過」就觸發一堆不必要的請求
    hoverTimer.current = setTimeout(async () => {
      setHoveredId(file.id);

      // 這個檔案的縮圖之前已經成功載入過，不用重打 API
      if (thumbnails[file.id]) return;

      try {
        const res = await fetch(`http://localhost:8000/api/files/${file.id}/thumbnail/`, {
          credentials: "include",
        });
        if (!res.ok) throw new Error("no thumbnail");

        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        setThumbnails((prev) => ({ ...prev, [file.id]: url }));
      } catch {
        setThumbnails((prev) => ({ ...prev, [file.id]: "error" }));
      }
    }, 200);
  }

  function handleMouseLeave() {
    clearTimeout(hoverTimer.current);
    setHoveredId(null);
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
          onMouseEnter={() => handleMouseEnter(f)}
          onMouseLeave={handleMouseLeave}
          style={{
            position: "relative",
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

          {/* 縮圖 tooltip：懸浮在滑鼠上方，只在 hover 且有東西可顯示時出現 */}
          {hoveredId === f.id && isPreviewable(f.mime_type) && (
            <div
              style={{
                position: "absolute",
                bottom: "100%",
                left: "1rem",
                marginBottom: "0.5rem",
                padding: "0.4rem",
                background: "#fff",
                border: "1px solid #ddd",
                borderRadius: "4px",
                boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
                zIndex: 10,
              }}
            >
              {thumbnails[f.id] === "error" ? (
                <span style={{ fontSize: "0.8rem", color: "#888" }}>
                  縮圖尚未產生
                </span>
              ) : thumbnails[f.id] ? (
                <img
                  src={thumbnails[f.id]}
                  alt={f.name}
                  style={{ maxWidth: "160px", maxHeight: "160px", display: "block" }}
                />
              ) : (
                <span style={{ fontSize: "0.8rem", color: "#888" }}>
                  載入中...
                </span>
              )}
            </div>
          )}
        </li>
      ))}
    </ul>
  );
}