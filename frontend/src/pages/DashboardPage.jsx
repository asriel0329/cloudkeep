import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { listSharedWithMe } from "../api/permissions";
import FolderBrowser from "../components/FolderBrowser";

export default function DashboardPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [sharedFolders, setSharedFolders] = useState([]);
  const [sharedLoading, setSharedLoading] = useState(true);
  const [sharedError, setSharedError] = useState(null);

  useEffect(() => {
    async function loadSharedFolders() {
      setSharedLoading(true);
      setSharedError(null);

      try {
        const data = await listSharedWithMe();
        setSharedFolders(data);
      } catch (err) {
        setSharedError(
          err.response?.data?.detail || "載入分享資料夾失敗"
        );
      } finally {
        setSharedLoading(false);
      }
    }

    loadSharedFolders();
  }, []);

  function openSharedFolder(folder) {
    navigate(`/folder/${folder.id}`);
  }

  return (
    <div
      style={{
        fontFamily: "sans-serif",
        padding: "2rem",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "1.5rem",
        }}
      >
        <h1 style={{ margin: 0 }}>CloudKeep</h1>

        <div>
          <span style={{ marginRight: "1rem" }}>
            {user.username}
          </span>

          <button onClick={logout}>
            登出
          </button>
        </div>
      </div>

      {/* 與我分享 */}
      <section
        style={{
          marginBottom: "2rem",
          padding: "1rem",
          border: "1px solid #ddd",
          borderRadius: "8px",
        }}
      >
        <h2 style={{ marginTop: 0 }}>與我分享</h2>

        {sharedLoading ? (
          <p>載入分享資料夾中...</p>
        ) : sharedError ? (
          <p style={{ color: "red" }}>{sharedError}</p>
        ) : sharedFolders.length === 0 ? (
          <p style={{ color: "#888" }}>
            目前沒有其他人分享給你的資料夾。
          </p>
        ) : (
          <ul
            style={{
              listStyle: "none",
              padding: 0,
              margin: 0,
            }}
          >
            {sharedFolders.map((folder) => (
              <li
                key={folder.id}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  padding: "0.75rem",
                  borderBottom: "1px solid #eee",
                }}
              >
                <div>
                  <button
                    onClick={() => openSharedFolder(folder)}
                    style={{
                      background: "none",
                      border: "none",
                      cursor: "pointer",
                      fontSize: "1rem",
                      padding: 0,
                    }}
                  >
                    📁 {folder.name}
                  </button>

                  <div
                    style={{
                      color: "#888",
                      fontSize: "0.85rem",
                      marginTop: "0.25rem",
                    }}
                  >
                    👤 擁有者：
                    {folder.owner?.username || `#${folder.owner}`}
                  </div>

                  <div
                    style={{
                      color:
                        folder.permission_level === "write"
                          ? "#2e7d32"
                          : "#666",
                      fontSize: "0.85rem",
                      marginTop: "0.25rem",
                    }}
                  >
                    🔐 權限：
                    {folder.permission_level === "write"
                      ? "可讀寫"
                      : "唯讀"}
                  </div>
                </div>

                <button
                  onClick={() => openSharedFolder(folder)}
                >
                  開啟
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* 我的檔案 */}
      <section>
        <h2>我的檔案</h2>

        <FolderBrowser />
      </section>
    </div>
  );
}