import client from "./client";

export async function listShares() {
  const res = await client.get("/shares/");
  return res.data;
}

export async function createShare({
  file = null,
  folder = null,
  permission_level = "read",
  expires_at = null,
  password = "",
}) {
  const data = {
    permission_level,
    expires_at,
    password,
  };

  if (file !== null) {
    data.file = file;
  }

  if (folder !== null) {
    data.folder = folder;
  }

  const res = await client.post("/shares/", data);
  return res.data;
}

export async function revokeShare(id) {
  await client.delete(`/shares/${id}/`);
}

export async function getPublicShare(token, password = "") {
  const params = {};

  if (password) {
    params.password = password;
  }

  const res = await client.get(`/shares/public/${token}/`, {
    params,
  });

  return res.data;
}

export async function downloadPublicShare(
  token,
  { password = "", fileId = null } = {}
) {
  const params = {};

  if (password) {
    params.password = password;
  }

  if (fileId !== null) {
    params.file = fileId;
  }

  const res = await client.get(`/shares/public/${token}/download/`, {
    params,
    responseType: "blob",
  });

  return {
    blob: res.data,
    filename:
      res.headers["content-disposition"] || null,
  };
}