import { useAuth } from "../context/AuthContext";

export default function DashboardPage() {
  const { user, logout } = useAuth();

  return (
    <div style={{ fontFamily: "sans-serif", padding: "2rem" }}>
      <h1>CloudKeep</h1>
      <p>歡迎，{user.username}（{user.email}）</p>
      <p>儲存配額：{(user.storage_quota_bytes / 1024 / 1024 / 1024).toFixed(1)} GB</p>
      <button onClick={logout}>登出</button>
      <hr />
      <p style={{ color: "#888" }}>資料夾與檔案瀏覽功能會在下一批（F2）加入。</p>
    </div>
  );
}