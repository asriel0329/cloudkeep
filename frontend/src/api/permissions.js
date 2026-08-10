import client from "./client";

export async function listPermissions(folderId) {
  const res = await client.get("/permissions/", {
    params: {
      folder: folderId,
    },
  });

  return res.data;
}

export async function createPermission(folderId, userId, level) {
  const res = await client.post("/permissions/", {
    folder: folderId,
    user: userId,
    level,
  });

  return res.data;
}

export async function revokePermission(id) {
  await client.delete(`/permissions/${id}/`);
}

export async function listSharedWithMe() {
  const res = await client.get("/permissions/shared-with-me/");
  return res.data;
}