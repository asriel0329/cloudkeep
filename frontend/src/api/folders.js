import client from "./client";

export async function listFolders(parentId) {
  const params = parentId ? { parent: parentId } : {};
  const res = await client.get("/folders/", { params });
  return res.data;
}

export async function getFolder(id) {
  const res = await client.get(`/folders/${id}/`);
  return res.data;
}

export async function createFolder(name, parentId) {
  const res = await client.post("/folders/", { name, parent: parentId ?? null });
  return res.data;
}