import client from "./client";

export async function register(data) {
  const res = await client.post("/auth/register/", data);
  return res.data;
}

export async function login(data) {
  const res = await client.post("/auth/login/", data);
  return res.data;
}

export async function logout() {
  await client.post("/auth/logout/");
}

export async function fetchMe() {
  const res = await client.get("/auth/me/");
  return res.data;
}