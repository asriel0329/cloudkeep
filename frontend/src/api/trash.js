import client from "./client";

export async function listTrashedFiles() {
  const res = await client.get("/files/trash/");
  return res.data;
}

export async function listTrashedFolders() {
  const res = await client.get("/folders/trash/");
  return res.data;
}

export async function restoreFile(id) {
  const res = await client.post(`/files/${id}/restore/`);
  return res.data;
}

export async function restoreFolder(id) {
  const res = await client.post(`/folders/${id}/restore/`);
  return res.data;
}

export async function permanentDeleteFile(id) {
  await client.delete(`/files/${id}/permanent/`);
}

export async function permanentDeleteFolder(id) {
  await client.delete(`/folders/${id}/permanent/`);
}

export async function emptyTrash() {
  await client.post("/files/trash/empty/");
}