import client from "./client";

const CHUNK_THRESHOLD = 20 * 1024 * 1024; // 超過 20MB 才走分塊上傳

export function shouldUseChunkedUpload(file) {
  return file.size > CHUNK_THRESHOLD;
}

export async function initUploadSession(file, folderId) {
  const res = await client.post("/files/upload/sessions/", {
    filename: file.name,
    size: file.size,
    mime_type: file.type || "application/octet-stream",
    folder: folderId ?? null,
  });
  return res.data; // { id, chunk_size, total_chunks, received_chunks }
}

export async function getSessionStatus(sessionId) {
  const res = await client.get(`/files/upload/sessions/${sessionId}/`);
  return res.data;
}

export async function uploadChunk(sessionId, chunkNumber, chunkBlob) {
  const formData = new FormData();
  formData.append("chunk", chunkBlob);
  const res = await client.put(
    `/files/upload/sessions/${sessionId}/chunks/${chunkNumber}/`,
    formData,
    { headers: { "Content-Type": "multipart/form-data" } }
  );
  return res.data; // { received_chunks, is_complete }
}

export async function completeUploadSession(sessionId) {
  const res = await client.post(`/files/upload/sessions/${sessionId}/complete/`);
  return res.data; // 完成後回傳的 File 物件，跟一般上傳的回應格式一樣
}

/**
 * 完整跑一次分塊上傳流程：建立 session -> 依序上傳每一塊 -> 全部到齊後 complete。
 * onProgress(percentage) 讓呼叫端可以顯示進度條。
 * 若中途失敗（例如網路斷線），拋出的 error 上會附帶 sessionId，
 * 讓呼叫端之後可以用 resumeUpload() 從中斷的地方接著傳，不用整個重來。
 */
export async function chunkedUpload(file, folderId, onProgress) {
  const session = await initUploadSession(file, folderId);
  return _uploadRemainingChunks(file, session, onProgress);
}

export async function resumeUpload(file, sessionId, onProgress) {
  const status = await getSessionStatus(sessionId);
  return _uploadRemainingChunks(file, status, onProgress);
}

async function _uploadRemainingChunks(file, session, onProgress) {
  const { id: sessionId, chunk_size: chunkSize, total_chunks: totalChunks } = session;
  let receivedChunks = new Set(session.received_chunks);

  onProgress?.(Math.round((receivedChunks.size / totalChunks) * 100));

  for (let i = 0; i < totalChunks; i++) {
    if (receivedChunks.has(i)) continue; // 這塊之前已經傳過了（斷線續傳的情況），跳過

    const start = i * chunkSize;
    const end = Math.min(start + chunkSize, file.size);
    const chunkBlob = file.slice(start, end);

    try {
      const result = await uploadChunk(sessionId, i, chunkBlob);
      receivedChunks = new Set(result.received_chunks);
      onProgress?.(Math.round((receivedChunks.size / totalChunks) * 100));
    } catch (err) {
      // 附上 sessionId，讓呼叫端能夠之後呼叫 resumeUpload(file, sessionId, ...) 接著傳
      err.sessionId = sessionId;
      throw err;
    }
  }

  return completeUploadSession(sessionId);
}