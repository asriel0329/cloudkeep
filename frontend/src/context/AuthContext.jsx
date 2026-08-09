import { createContext, useContext, useEffect, useState } from "react";
import { ensureCsrfCookie } from "../api/csrf";
import {
  fetchMe,
  login as apiLogin,
  logout as apiLogout,
  register as apiRegister,
} from "../api/auth";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // App 一啟動就先確保有 CSRF cookie，再問後端「現在是誰登入」
  // （如果瀏覽器上次的 session 還沒過期，這裡就能直接恢復登入狀態，
  // 使用者不用每次重新整理頁面都要重新登入）。
  useEffect(() => {
    async function init() {
      await ensureCsrfCookie();
      try {
        const me = await fetchMe();
        setUser(me);
      } catch {
        setUser(null);
      } finally {
        setLoading(false);
      }
    }
    init();
  }, []);

  async function login(username, password) {
    const data = await apiLogin({ username, password });
    setUser(data);
  }

  async function register(payload) {
    const data = await apiRegister(payload);
    setUser(data);
  }

  async function logout() {
    await apiLogout();
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}