import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ username: "", email: "", password: "" });
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  function handleChange(e) {
    setForm({ ...form, [e.target.name]: e.target.value });
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await register(form);
      navigate("/");
    } catch (err) {
      const data = err.response?.data;
      setError(data ? JSON.stringify(data) : "註冊失敗");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div style={{ maxWidth: 320, margin: "4rem auto", fontFamily: "sans-serif" }}>
      <h1>註冊 CloudKeep</h1>
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: "1rem" }}>
          <label>帳號</label>
          <input
            name="username"
            value={form.username}
            onChange={handleChange}
            style={{ width: "100%", padding: "0.5rem" }}
            required
          />
        </div>
        <div style={{ marginBottom: "1rem" }}>
          <label>Email</label>
          <input
            type="email"
            name="email"
            value={form.email}
            onChange={handleChange}
            style={{ width: "100%", padding: "0.5rem" }}
            required
          />
        </div>
        <div style={{ marginBottom: "1rem" }}>
          <label>密碼（至少 8 碼）</label>
          <input
            type="password"
            name="password"
            value={form.password}
            onChange={handleChange}
            style={{ width: "100%", padding: "0.5rem" }}
            required
          />
        </div>
        {error && <p style={{ color: "red" }}>{error}</p>}
        <button type="submit" disabled={submitting} style={{ width: "100%", padding: "0.5rem" }}>
          {submitting ? "註冊中..." : "註冊"}
        </button>
      </form>
      <p style={{ marginTop: "1rem" }}>
        已經有帳號了？<Link to="/login">登入</Link>
      </p>
    </div>
  );
}