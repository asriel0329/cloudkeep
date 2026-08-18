import { useRef, useState } from "react";
import { uploadFile } from "../api/files";
import { chunkedUpload, resumeUpload, shouldUseChunkedUpload } from "../api/chunkedUpload";
import {
  collectFromDataTransferItems,
  collectFromInputFileList,
  createFolderResolver,
  resolveFolderPath,
} from "../api/folderUpload";

export default function FileUploader({ folderId, onUploaded, onFolderCreated }) {
  const [dragging, setDragging] = useState(false);
  const [uploads, setUploads] = useState([]); // [{ id, file, name, folderId, progress, error, sessionId }]
  const fileInputRef = useRef(null);
  const folderInputRef = useRef(null);

  function updateEntry(entryId, patch) {
    setUploads((prev) => prev.map((u) => (u.id === entryId ? { ...u, ...patch } : u)));
  }

  async function runOne(entryId, file, targetFolderId, resumeSessionId) {
    const onProgress = (progress) => updateEntry(entryId, { progress });

    try {
      if (resumeSessionId) {
        await resumeUpload(file, resumeSessionId, onProgress);
      } else if (shouldUseChunkedUpload(file)) {
        await chunkedUpload(file, targetFolderId, onProgress);
      } else {
        await uploadFile(file, targetFolderId, (evt) => {
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

      updateEntry(entryId, { error: message, sessionId: err.sessionId || null });
    }
  }

  /**
   * entries: [{ relativePath, file }]
   * 這是資料夾上傳跟一般上傳共用的核心處理函式：
   * 先把每個檔案的資料夾路徑解析/建立出來，再逐一觸發上傳。
   */
  async function processEntries(entries) {
    if (entries.length === 0) return;

    const resolver = createFolderResolver();
    const hasNestedPath = entries.some((e) => e.relativePath.includes("/"));

    const prepared = await Promise.all(
      entries.map(async (entry) => {
        const segments = entry.relativePath.split("/");
        const filename = segments.pop();
        const targetFolderId =
          segments.length === 0
            ? folderId ?? null
            : await resolveFolderPath(resolver, segments, folderId);

        return { file: entry.file, name: filename, targetFolderId };
      })
    );

    // 有建立新資料夾的話，通知上層刷新資料夾樹狀列表
    if (hasNestedPath) {
      onFolderCreated?.();
    }

    const newUploads = prepared.map(({ file, name, targetFolderId }) => ({
      id: `${name}-${file.size}-${Date.now()}-${Math.random()}`,
      file,
      name,
      folderId: targetFolderId,
      progress: 0,
      error: null,
      sessionId: null,
    }));

    setUploads((prev) => [...prev, ...newUploads]);

    await Promise.all(
      newUploads.map((entry) => runOne(entry.id, entry.file, entry.folderId))
    );
  }

  function handleRetry(entry) {
    updateEntry(entry.id, { error: null });
    runOne(entry.id, entry.file, entry.folderId, entry.sessionId);
  }

  async function handleDrop(e) {
    e.preventDefault();
    setDragging(false);

    const items = e.dataTransfer.items;
    if (items && items.length > 0 && items[0].webkitGetAsEntry) {
      const entries = await collectFromDataTransferItems(items);
      processEntries(entries);
      return;
    }

    // 不支援 items API 的舊瀏覽器，退回成單純的檔案清單（不支援資料夾）
    const entries = Array.from(e.dataTransfer.files).map((file) => ({
      relativePath: file.name,
      file,
    }));
    processEntries(entries);
  }

  function handleFileChange(e) {
    const entries = Array.from(e.target.files).map((file) => ({
      relativePath: file.name,
      file,
    }));
    processEntries(entries);
    e.target.value = "";
  }

  function handleFolderChange(e) {
    const entries = collectFromInputFileList(e.target.files);
    processEntries(entries);
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
        style={{
          border: `2px dashed ${dragging ? "#4a90e2" : "#ccc"}`,
          borderRadius: "8px",
          padding: "1.5rem",
          textAlign: "center",
          color: "#888",
          background: dragging ? "#f0f7ff" : "transparent",
        }}
      >
        將檔案或資料夾拖曳到這裡上傳
        <div style={{ marginTop: "0.75rem", display: "flex", gap: "0.5rem", justifyContent: "center" }}>
          <button onClick={() => fileInputRef.current?.click()}>選擇檔案</button>
          <button onClick={() => folderInputRef.current?.click()}>選擇資料夾</button>
        </div>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          onChange={handleFileChange}
          style={{ display: "none" }}
        />
        <input
          ref={folderInputRef}
          type="file"
          webkitdirectory=""
          directory=""
          onChange={handleFolderChange}
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