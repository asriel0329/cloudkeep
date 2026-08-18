import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  listTrashedFiles,
  listTrashedFolders,
  permanentDeleteFile,
  permanentDeleteFolder,
  restoreFile,
  restoreFolder,
  emptyTrash,
} from "../api/trash";

export default function TrashPage() {
  const [files, setFiles] = useState([]);
  const [folders, setFolders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busyKey, setBusyKey] = useState(null);

  async function load() {
    setLoading(true);
    const [f, d] = await Promise.all([listTrashedFiles(), listTrashedFolders()]);
    setFiles(f);
    setFolders(d);
    setLoading(false);
  }

  useEffect(() => {
    load();
  }, []);

  async function handleRestoreFile(file) {
    setBusyKey(`file-${file.id}`);
    try {
      await restoreFile(file.id);
      await load();
    } finally {
      setBusyKey(null);
    }
  }

  async function handleRestoreFolder(folder) {
    setBusyKey(`folder-${folder.id}`);
    try {
      await restoreFolder(folder.id);
      await load();
    } finally {
      setBusyKey(null);
    }
  }

  async function handlePurgeFile(file) {
    if (!window.confirm(`「${file.name}」將被永久刪除，無法復原，確定嗎？`)) return;
    setBusyKey(`file-${file.id}`);
    try {
      await permanentDeleteFile(file.id);
      await load();
    } finally {
      setBusyKey(null);
    }
  }

  async function handlePurgeFolder(folder) {
    if (!window.confirm(`「${folder.name}」及其中所有內容將被永久刪除，無法復原，確定嗎？`)) return;
    setBusyKey(`folder-${folder.id}`);
    try {
      await permanentDeleteFolder(folder.id);
      await load();
    } finally {
      setBusyKey(null);
    }
  }

  async function handleEmptyTrash() {
    if (!window.confirm("確定要清空回收桶嗎？裡面所有的檔案與資料夾將被永久刪除，無法復原。")) return;
    setBusyKey("empty-trash");
    try {
      await emptyTrash();
      await load();
    } finally {
      setBusyKey(null);
    }
  }

  if (loading) return <p style={{ padding: "2rem" }}>載入中...</p>;

  return (
    <div style={{ fontFamily: "sans-serif", padding: "2rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h1>回收桶</h1>
        <div style={{ display: "flex", gap: "1rem", alignItems: "center" }}>
          {(files.length > 0 || folders.length > 0) && (
            <button
              onClick={handleEmptyTrash}
              disabled={busyKey === "empty-trash"}
              style={{ color: "red" }}
            >
              🗑 清空回收桶
            </button>
          )}
          <Link to="/">⬅ 回到我的檔案</Link>
        </div>
      </div>

      <h2>資料夾</h2>
      {folders.length === 0 ? (
        <p style={{ color: "#888" }}>回收桶裡沒有資料夾。</p>
      ) : (
        <ul style={{ listStyle: "none", padding: 0 }}>
          {folders.map((f) => (
            <li key={f.id} style={{ display: "flex", justifyContent: "space-between", padding: "0.5rem", borderBottom: "1px solid #eee" }}>
              <span>📁 {f.name}</span>
              <div style={{ display: "flex", gap: "0.4rem" }}>
                <button onClick={() => handleRestoreFolder(f)} disabled={busyKey === `folder-${f.id}`}>還原</button>
                <button onClick={() => handlePurgeFolder(f)} disabled={busyKey === `folder-${f.id}`} style={{ color: "red" }}>永久刪除</button>
              </div>
            </li>
          ))}
        </ul>
      )}

      <h2 style={{ marginTop: "2rem" }}>檔案</h2>
      {files.length === 0 ? (
        <p style={{ color: "#888" }}>回收桶裡沒有檔案。</p>
      ) : (
        <ul style={{ listStyle: "none", padding: 0 }}>
          {files.map((f) => (
            <li key={f.id} style={{ display: "flex", justifyContent: "space-between", padding: "0.5rem", borderBottom: "1px solid #eee" }}>
              <span>📄 {f.name}</span>
              <div style={{ display: "flex", gap: "0.4rem" }}>
                <button onClick={() => handleRestoreFile(f)} disabled={busyKey === `file-${f.id}`}>還原</button>
                <button onClick={() => handlePurgeFile(f)} disabled={busyKey === `file-${f.id}`} style={{ color: "red" }}>永久刪除</button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}