import { useEffect, useState } from "react";
import { fetchQuota } from "../api/quota";

function formatGB(bytes) {
  return (bytes / 1024 / 1024 / 1024).toFixed(2);
}

export default function QuotaBar() {
  const [quota, setQuota] = useState(null);

  useEffect(() => {
    fetchQuota().then(setQuota).catch(() => {});
  }, []);

  if (!quota) return null;

  return (
    <div style={{ margin: "1rem 0" }}>
      <div style={{ fontSize: "0.85rem", color: "#666", marginBottom: "0.3rem" }}>
        已使用 {formatGB(quota.used_bytes)} GB / {formatGB(quota.quota_bytes)} GB
      </div>
      <div style={{ background: "#eee", borderRadius: "4px", height: "8px", overflow: "hidden" }}>
        <div
          style={{
            width: `${Math.min(quota.percentage, 100)}%`,
            background: quota.percentage > 90 ? "#e53e3e" : "#3182ce",
            height: "100%",
          }}
        />
      </div>
    </div>
  );
}