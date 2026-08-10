import { useAuth } from "../context/AuthContext";
import FolderBrowser from "../components/FolderBrowser";

export default function DashboardPage() {
  const { user, logout } = useAuth();

  return (
    <div style={{ fontFamily: "sans-serif", padding: "2rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h1>CloudKeep</h1>
        <div>
          <span style={{ marginRight: "1rem" }}>{user.username}</span>
          <button onClick={logout}>登出</button>
        </div>
      </div>
      <FolderBrowser />
    </div>
  );
}