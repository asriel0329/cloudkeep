import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import {
  createFolder,
  getFolder,
  listFolders,
} from "../api/folders";

import {
  listFiles,
  deleteFile,
  downloadFile,
} from "../api/files";

import FileUploader from "./FileUploader";
import FileList from "./FileList";
import ShareModal from "./ShareModal";
import PermissionModal from "./PermissionModal";

export default function FolderBrowser() {
  const { folderId } = useParams();
  const navigate = useNavigate();

  const [folder, setFolder] = useState(null);
  const [subfolders, setSubfolders] = useState([]);
  const [files, setFiles] = useState([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [newFolderName, setNewFolderName] = useState("");
  const [creating, setCreating] = useState(false);

  const [shareTarget, setShareTarget] = useState(null);
  const [permissionTarget, setPermissionTarget] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);

      try {
        const [
          folderData,
          subfolderData,
          fileData,
        ] = await Promise.all([
          folderId
            ? getFolder(folderId)
            : Promise.resolve(null),
          listFolders(folderId),
          listFiles(folderId),
        ]);

        if (!cancelled) {
          setFolder(folderData);
          setSubfolders(subfolderData);
          setFiles(fileData);
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err.response?.data?.detail ||
              "載入資料夾失敗"
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    load();

    return () => {
      cancelled = true;
    };
  }, [folderId]);

  async function refreshFiles() {
    const fileData = await listFiles(folderId);
    setFiles(fileData);
  }

  async function refreshFolders() {
    const refreshed = await listFolders(folderId);
    setSubfolders(refreshed);
  }

  async function handleDownload(file) {
    const blob = await downloadFile(file.id);

    const url = window.URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = file.name;

    document.body.appendChild(a);
    a.click();
    a.remove();

    window.URL.revokeObjectURL(url);
  }

  async function handleDeleteFile(file) {
    await deleteFile(file.id);

    setFiles((prev) =>
      prev.filter((f) => f.id !== file.id)
    );
  }

  async function handleCreateFolder(e) {
    e.preventDefault();

    if (!newFolderName.trim()) {
      return;
    }

    setCreating(true);
    setError(null);

    try {
      await createFolder(
        newFolderName.trim(),
        folderId ?? null
      );

      setNewFolderName("");
      await refreshFolders();
    } catch (err) {
      setError(
        err.response?.data?.name?.[0] ||
          err.response?.data?.detail ||
          "建立資料夾失敗"
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

  if (loading) {
    return <p>載入中...</p>;
  }

  return (
    <div>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "1rem",
          marginBottom: "1rem",
        }}
      >
        <h2 style={{ margin: 0 }}>
          {folder ? folder.name : "根目錄"}
        </h2>

        {folder && (
          <button onClick={goUp}>
            ⬆ 上一層
          </button>
        )}

        {folder && (
          <>
            <button
              onClick={() => setShareTarget({
                type: "folder",
                data: folder,
              })}
            >
              🔗 分享
            </button>

            <button
              onClick={() => setPermissionTarget(folder)}
            >
              👥 管理權限
            </button>
          </>
        )}
      </div>

      <form
        onSubmit={handleCreateFolder}
        style={{
          marginBottom: "1rem",
          display: "flex",
          gap: "0.5rem",
        }}
      >
        <input
          value={newFolderName}
          onChange={(e) =>
            setNewFolderName(e.target.value)
          }
          placeholder="新資料夾名稱"
        />

        <button type="submit" disabled={creating}>
          {creating
            ? "建立中..."
            : "新增資料夾"}
        </button>
      </form>

      {error && (
        <p style={{ color: "red" }}>
          {error}
        </p>
      )}

      {subfolders.length === 0 ? (
        <p style={{ color: "#888" }}>
          這裡還沒有任何資料夾。
        </p>
      ) : (
        <ul
          style={{
            listStyle: "none",
            padding: 0,
          }}
        >
          {subfolders.map((f) => (
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
              <button
                onClick={() => openFolder(f.id)}
                style={{
                  background: "none",
                  border: "none",
                  cursor: "pointer",
                  fontSize: "1rem",
                }}
              >
                📁 {f.name}
              </button>

              <div
                style={{
                  display: "flex",
                  gap: "0.4rem",
                }}
              >
                <button
                  onClick={() =>
                    setShareTarget({
                      type: "folder",
                      data: f,
                    })
                  }
                >
                  分享
                </button>

                <button
                  onClick={() =>
                    setPermissionTarget(f)
                  }
                >
                  權限管理
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}

      <hr />

      <FileUploader
        folderId={folderId}
        onUploaded={refreshFiles}
      />

      <FileList
        files={files}
        onDownload={handleDownload}
        onDelete={handleDeleteFile}
        onShare={(file) =>
          setShareTarget({
            type: "file",
            data: file,
          })
        }
      />

      {shareTarget && (
        <ShareModal
          file={
            shareTarget.type === "file"
              ? shareTarget.data
              : null
          }
          folder={
            shareTarget.type === "folder"
              ? shareTarget.data
              : null
          }
          onClose={() => setShareTarget(null)}
        />
      )}

      {permissionTarget && (
        <PermissionModal
          folder={permissionTarget}
          onClose={() =>
            setPermissionTarget(null)
          }
        />
      )}
    </div>
  );
}