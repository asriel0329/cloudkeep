import { useRef, useState } from "react";
import { uploadFile } from "../api/files";
import { chunkedUpload, resumeUpload, shouldUseChunkedUpload } from "../api/chunkedUpload";

export default function FileUploader({ folderId, onUploaded }) {
  const [dragging, setDragging] = useState(false);
  const [uploads, setUploads] = useState([]); // [{ id, file, name, progress, error, sessionId }]
  const inputRef = useRef(null);

  function updateEntry(entryId, patch) {
    setUploads((prev) => prev.map((u) => (u.id === entryId ? { ...u, ...patch } : u)));
  }

  async function runOne(entryId, file, resumeSessionId) {
    const onProgress = (progress) => updateEntry(entryId, { progress });

    try {
      if (resumeSessionId) {
        // 之前中斷過，這次只補傳缺的分塊，不是從頭重來
        await resumeUpload(file, resumeSessionId, onProgress);
      } else if (shouldUseChunkedUpload(file)) {
        await chunkedUpload(file, folderId, onProgress);
      } else {
        await uploadFile(file, folderId, (evt) => {
          if (!evt.total) return;
          onProgress(Math.round((evt.loaded / evt.total) * 100));
        });
      }

      setUploads((prev) => prev.filter((u) => u.id !== entryId));
      onUploaded?.();
    } catch (err) {
      const message =
        err.response?.data?.file?.[0] ||
        err.response?.data?.folder?.[0] ||
        err.response?.data?.detail ||
        "上傳失敗，可能是網路中斷";

      // 分塊上傳失敗時，err 上會附帶 sessionId，讓使用者可以點「接著傳」，
      // 只補傳缺的部分；一般上傳失敗則沒有 sessionId，只能整個重試。
      updateEntry(entryId, { error: message, sessionId: err.sessionId || null });
    }
  }

  async function uploadFiles(fileList) {
    const files = Array.from(fileList);
    if (files.length === 0) return;

    const entries = files.map((file) => ({
      id: `${file.name}-${file.size}-${Date.now()}-${Math.random()}`,
      file,
      name: file.name,
      progress: 0,
      error: null,
      sessionId: null,
    }));
    setUploads((prev) => [...prev, ...entries]);

    await Promise.all(entries.map((entry) => runOne(entry.id, entry.file)));
  }

  function handleRetry(entry) {
    updateEntry(entry.id, { error: null });
    runOne(entry.id, entry.file, entry.sessionId);
  }

  function handleDrop(e) {
    e.preventDefault();
    setDragging(false);
    uploadFiles(e.dataTransfer.files);
  }

  function handleChange(e) {
    uploadFiles(e.target.files);
    e.target.value = "";
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
                <span style={{ color: "red" }}>
                  ❌ {u.name}：{u.error}{" "}
                  <button onClick={() => handleRetry(u)} style={{ fontSize: "0.8rem" }}>
                    {u.sessionId ? "接著傳" : "重試"}
                  </button>
                </span>
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