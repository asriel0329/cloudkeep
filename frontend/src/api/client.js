import axios from "axios";

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  withCredentials: true,      // 讓瀏覽器帶著 cookie（session、CSRF）一起送
  xsrfCookieName: "csrftoken",
  xsrfHeaderName: "X-CSRFToken",
  withXSRFToken: true,        // 前後端是不同 port，算不同 origin，要明確開啟
});

export default client;