import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import {
  getPublicShare,
  downloadPublicShare,
} from "../api/shares";

export default function PublicSharePage() {
  const { token } = useParams();

  const [share, setShare] = useState(null);
  const [password, setPassword] = useState("");
  const [passwordRequired, setPasswordRequired] =
    useState(false);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [downloadingId, setDownloadingId] =
    useState(null);

  async function loadShare(inputPassword = "") {
    setLoading(true);
    setError(null);

    try {
      const data = await getPublicShare(
        token,
        inputPassword
      );

      setShare(data);
      setPasswordRequired(false);
    } catch (err) {
      if (err.response?.status === 401) {
        setPasswordRequired(true);
        setShare(null);
      } else if (err.response?.status === 404) {
        setError("分享連結不存在或已經過期。");
      } else {
        setError(
          err.response?.data?.detail ||
            "載入分享內容失敗"
        );
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadShare();
  }, [token]);

  async function handlePasswordSubmit(e) {
    e.preventDefault();

    if (!password) {
      return;
    }

    await loadShare(password);
  }

  async function handleDownload(file) {
    setDownloadingId(file.id);
    setError(null);

    try {
      const result = await downloadPublicShare(
        token,
        {
          password,
          fileId:
            share.type === "folder"
              ? file.id
              : null,
        }
      );

      const url = window.URL.createObjectURL(
        result.blob
      );

      const a = document.createElement("a");
      a.href = url;
      a.download = file.name;

      document.body.appendChild(a);
      a.click();
      a.remove();

      window.URL.revokeObjectURL(url);
    } catch (err) {
      if (err.response?.status === 401) {
        setPasswordRequired(true);
        setShare(null);
      } else {
        setError("下載失敗");
      }
    } finally {
      setDownloadingId(null);
    }
  }

  if (loading) {
    return (
      <div style={{ padding: "2rem" }}>
        載入中...
      </div>
    );
  }

  if (passwordRequired) {
    return (
      <div
        style={{
          maxWidth: "400px",
          margin: "4rem auto",
          padding: "2rem",
          fontFamily: "sans-serif",
        }}
      >
        <h2>此分享連結需要密碼</h2>

        <form onSubmit={handlePasswordSubmit}>
          <input
            type="password"
            value={password}
            onChange={(e) =>
              setPassword(e.target.value)
            }
            placeholder="輸入分享密碼"
            style={{
              width: "100%",
              padding: "0.7rem",
              boxSizing: "border-box",
              marginBottom: "1rem",
            }}
            autoFocus
          />

          <button type="submit">
            驗證密碼
          </button>
        </form>

        {error && (
          <p style={{ color: "red" }}>
            {error}
          </p>
        )}
      </div>
    );
  }

  if (error) {
    return (
      <div
        style={{
          padding: "2rem",
          fontFamily: "sans-serif",
        }}
      >
        <h2>無法開啟分享</h2>
        <p style={{ color: "red" }}>
          {error}
        </p>
      </div>
    );
  }

  if (!share) {
    return null;
  }

  if (share.type === "file") {
    const file = share.file;

    return (
      <div
        style={{
          maxWidth: "700px",
          margin: "3rem auto",
          padding: "2rem",
          fontFamily: "sans-serif",
        }}
      >
        <h1>CloudKeep 分享</h1>

        <div
          style={{
            border: "1px solid #ddd",
            borderRadius: "8px",
            padding: "1.5rem",
          }}
        >
          <h2>{file.name}</h2>

          <p>
            權限：
            {share.permission_level === "write"
              ? "可讀寫"
              : "唯讀"}
          </p>

          <button
            onClick={() => handleDownload(file)}
            disabled={downloadingId === file.id}
          >
            {downloadingId === file.id
              ? "下載中..."
              : "下載檔案"}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div
      style={{
        maxWidth: "800px",
        margin: "3rem auto",
        padding: "2rem",
        fontFamily: "sans-serif",
      }}
    >
      <h1>CloudKeep 分享</h1>

      <h2>
        📁 {share.folder.name}
      </h2>

      <p>
        權限：
        {share.permission_level === "write"
          ? "可讀寫"
          : "唯讀"}
      </p>

      <h3>檔案</h3>

      {share.files.length === 0 ? (
        <p style={{ color: "#888" }}>
          此資料夾沒有檔案。
        </p>
      ) : (
        <ul
          style={{
            listStyle: "none",
            padding: 0,
          }}
        >
          {share.files.map((file) => (
            <li
              key={file.id}
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                padding: "0.75rem",
                borderBottom:
                  "1px solid #eee",
              }}
            >
              <span>
                📄 {file.name}
              </span>

              <button
                onClick={() =>
                  handleDownload(file)
                }
                disabled={
                  downloadingId === file.id
                }
              >
                {downloadingId === file.id
                  ? "下載中..."
                  : "下載"}
              </button>
            </li>
          ))}
        </ul>
      )}

      <h3>子資料夾</h3>

      {share.subfolders.length === 0 ? (
        <p style={{ color: "#888" }}>
          沒有子資料夾。
        </p>
      ) : (
        <ul>
          {share.subfolders.map((folder) => (
            <li key={folder.id}>
              📁 {folder.name}
            </li>
          ))}
        </ul>
      )}

      {error && (
        <p style={{ color: "red" }}>
          {error}
        </p>
      )}
    </div>
  );
}