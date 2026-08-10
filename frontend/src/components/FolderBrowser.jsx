import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { createFolder, getFolder, listFolders } from "../api/folders";

export default function FolderBrowser() {
  // folderId 從網址取得，例如 /folder/5 -> folderId = "5"
  // 在根目錄時（網址是 /），folderId 會是 undefined
  const { folderId } = useParams();
  const navigate = useNavigate();

  const [folder, setFolder] = useState(null); // 目前資料夾本身的資訊，根目錄時是 null
  const [subfolders, setSubfolders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [newFolderName, setNewFolderName] = useState("");
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [folderData, subfolderData] = await Promise.all([
          folderId ? getFolder(folderId) : Promise.resolve(null),
          listFolders(folderId),
        ]);
        if (!cancelled) {
          setFolder(folderData);
          setSubfolders(subfolderData);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.response?.data?.detail || "載入資料夾失敗");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    // 元件被拆掉或 folderId 又變了的時候，避免舊的請求結果覆蓋新的畫面
    return () => {
      cancelled = true;
    };
  }, [folderId]);

  async function handleCreateFolder(e) {
    e.preventDefault();
    if (!newFolderName.trim()) return;

    setCreating(true);
    setError(null);
    try {
      await createFolder(newFolderName.trim(), folderId ?? null);
      setNewFolderName("");
      const refreshed = await listFolders(folderId);
      setSubfolders(refreshed);
    } catch (err) {
      setError(
        err.response?.data?.name?.[0] || err.response?.data?.detail || "建立資料夾失敗"
      );
    } finally {
      setCreating(false);
    }
  }

  function openFolder(id) {
    navigate(`/folder/${id}`);
  }

  function goUp() {
    if (folder?.parent) {
      navigate(`/folder/${folder.parent}`);
    } else {
      navigate("/");
    }
  }

  if (loading) return <p>載入中...</p>;

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", gap: "1rem", marginBottom: "1rem" }}>
        <h2 style={{ margin: 0 }}>{folder ? folder.name : "根目錄"}</h2>
        {folder && <button onClick={goUp}>⬆ 上一層</button>}
      </div>

      <form onSubmit={handleCreateFolder} style={{ marginBottom: "1rem", display: "flex", gap: "0.5rem" }}>
        <input
          value={newFolderName}
          onChange={(e) => setNewFolderName(e.target.value)}
          placeholder="新資料夾名稱"
        />
        <button type="submit" disabled={creating}>
          {creating ? "建立中..." : "新增資料夾"}
        </button>
      </form>

      {error && <p style={{ color: "red" }}>{error}</p>}

      {subfolders.length === 0 ? (
        <p style={{ color: "#888" }}>這裡還沒有任何資料夾。</p>
      ) : (
        <ul style={{ listStyle: "none", padding: 0 }}>
          {subfolders.map((f) => (
            <li key={f.id} style={{ padding: "0.5rem", borderBottom: "1px solid #eee" }}>
              <button
                onClick={() => openFolder(f.id)}
                style={{ background: "none", border: "none", cursor: "pointer", fontSize: "1rem" }}
              >
                📁 {f.name}
              </button>
            </li>
          ))}
        </ul>
      )}

      <hr />
      <p style={{ color: "#888" }}>檔案上傳/下載功能會在下一批（F3）加入。</p>
    </div>
  );
}