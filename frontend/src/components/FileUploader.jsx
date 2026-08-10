import { useRef, useState } from "react";
import { uploadFile } from "../api/files";

export default function FileUploader({ folderId, onUploaded }) {
  const [dragging, setDragging] = useState(false);
  const [uploads, setUploads] = useState([]); // [{ id, name, progress, error }]
  const inputRef = useRef(null);

  async function uploadFiles(fileList) {
    const files = Array.from(fileList);
    if (files.length === 0) return;

    const entries = files.map((file) => ({
      id: `${file.name}-${file.size}-${Date.now()}-${Math.random()}`,
      name: file.name,
      progress: 0,
      error: null,
    }));
    setUploads((prev) => [...prev, ...entries]);

    await Promise.all(
      files.map((file, idx) => {
        const entryId = entries[idx].id;
        return uploadFile(file, folderId, (evt) => {
          if (!evt.total) return;
          const progress = Math.round((evt.loaded / evt.total) * 100);
          setUploads((prev) =>
            prev.map((u) => (u.id === entryId ? { ...u, progress } : u))
          );
        })
          .then(() => {
            setUploads((prev) => prev.filter((u) => u.id !== entryId));
            onUploaded?.();
          })
          .catch((err) => {
            const message =
              err.response?.data?.file?.[0] ||
              err.response?.data?.folder?.[0] ||
              err.response?.data?.detail ||
              "上傳失敗";
            setUploads((prev) =>
              prev.map((u) => (u.id === entryId ? { ...u, error: message } : u))
            );
          });
      })
    );
  }

  function handleDrop(e) {
    e.preventDefault();
    setDragging(false);
    uploadFiles(e.dataTransfer.files);
  }

  function handleChange(e) {
    uploadFiles(e.target.files);
    e.target.value = ""; // 允許重複選同一個檔案
  }

  return (
    <div style={{ marginBottom: "1rem" }}>
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        style={{
          border: `2px dashed ${dragging ? "#4a90e2" : "#ccc"}`,
          borderRadius: "8px",
          padding: "1.5rem",
          textAlign: "center",
          color: "#888",
          cursor: "pointer",
          background: dragging ? "#f0f7ff" : "transparent",
        }}
      >
        將檔案拖曳到這裡上傳，或點擊選擇檔案
        <input
          ref={inputRef}
          type="file"
          multiple
          onChange={handleChange}
          style={{ display: "none" }}
        />
      </div>

      {uploads.length > 0 && (
        <ul style={{ listStyle: "none", padding: 0, marginTop: "0.5rem" }}>
          {uploads.map((u) => (
            <li key={u.id} style={{ fontSize: "0.85rem", padding: "0.25rem 0" }}>
              {u.error ? (
                <span style={{ color: "red" }}>❌ {u.name}：{u.error}</span>
              ) : (
                <span>⬆ {u.name}（{u.progress}%）</span>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}