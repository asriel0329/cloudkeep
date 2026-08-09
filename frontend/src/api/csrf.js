import client from "./client";

// 打這支 API 純粹是為了讓 Django 在回應裡塞一個 csrftoken cookie
// 進瀏覽器。之後任何 POST/PATCH/DELETE 請求，axios 都會自動從這個
// cookie 讀出值、夾帶到 X-CSRFToken header 裡，不用手動處理。
export async function ensureCsrfCookie() {
  await client.get("/auth/csrf/");
}