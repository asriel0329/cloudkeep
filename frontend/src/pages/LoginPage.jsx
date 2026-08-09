import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(username, password);
      navigate("/");
    } catch (err) {
      setError(err.response?.data?.detail || "登入失敗，請確認帳號密碼");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div style={{ maxWidth: 320, margin: "4rem auto", fontFamily: "sans-serif" }}>
      <h1>登入 CloudKeep</h1>
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: "1rem" }}>
          <label>帳號</label>
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            style={{ width: "100%", padding: "0.5rem" }}
            required
          />
        </div>
        <div style={{ marginBottom: "1rem" }}>
          <label>密碼</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={{ width: "100%", padding: "0.5rem" }}
            required
          />
        </div>
        {error && <p style={{ color: "red" }}>{error}</p>}
        <button type="submit" disabled={submitting} style={{ width: "100%", padding: "0.5rem" }}>
          {submitting ? "登入中..." : "登入"}
        </button>
      </form>
      <p style={{ marginTop: "1rem" }}>
        還沒有帳號？<Link to="/register">註冊</Link>
      </p>
    </div>
  );
}