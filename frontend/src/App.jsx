import { useEffect, useState } from "react";
import client from "./api/client";
import { ensureCsrfCookie } from "./api/csrf";

function App() {
  const [status, setStatus] = useState("連線中...");
  const [error, setError] = useState(null);

  useEffect(() => {
    async function checkConnection() {
      try {
        await ensureCsrfCookie();
        const res = await client.get("/health/");
        setStatus(res.data.status);
      } catch (err) {
        setError(err.message);
      }
    }
    checkConnection();
  }, []);

  return (
    <div style={{ fontFamily: "sans-serif", padding: "2rem" }}>
      <h1>CloudKeep</h1>
      {error ? (
        <p style={{ color: "red" }}>連線失敗：{error}</p>
      ) : (
        <p>後端狀態：{status}</p>
      )}
    </div>
  );
}

export default App;