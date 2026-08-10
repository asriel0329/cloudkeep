import client from "./client";

export async function listFiles(folderId) {
  const params = folderId ? { folder: folderId } : {};
  const res = await client.get("/files/", { params });
  return res.data;
}

export async function uploadFile(file, folderId, onUploadProgress) {
  const formData = new FormData();
  formData.append("file", file);
  if (folderId) {
    formData.append("folder", folderId);
  }
  const res = await client.post("/files/upload/", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress,
  });
  return res.data;
}

export async function deleteFile(id) {
  await client.delete(`/files/${id}/`);
}

// 回傳 blob，交給呼叫端決定怎麼觸發下載（檔名要另外從 file.name 帶）
export async function downloadFile(id) {
  const res = await client.get(`/files/${id}/download/`, {
    responseType: "blob",
  });
  return res.data;
}