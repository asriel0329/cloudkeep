import client from "./client";

export async function fetchQuota() {
  const res = await client.get("/files/quota/");
  return res.data;
}