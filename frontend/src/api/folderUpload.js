import { createFolder, listFolders } from "./folders";

/**
 * 建立一個「資料夾路徑解析器」，內部用 cache 記住已經解析/建立過的路徑，
 * 避免同一個資料夾被重複檢查、甚至重複建立（例如同一層底下有 20 個檔案，
 * 不需要為了每個檔案都各自打一次 API 去確認/建立同一個資料夾）。
 *
 * cache 存的是 Promise 而不是直接存 id，是為了處理「同時間有好幾個檔案
 * 都在問同一個路徑」的情況：第一個問的人觸發真正的 API 呼叫，
 * 後面幾個直接拿到同一個 Promise，等它 resolve，不會各自重複建立。
 */
export function createFolderResolver() {
  const cache = new Map();

  async function resolveOne(name, parentId) {
    const key = `${parentId ?? "root"}::${name}`;
    if (cache.has(key)) return cache.get(key);

    const promise = (async () => {
      const siblings = await listFolders(parentId ?? undefined);
      const existing = siblings.find((f) => f.name === name);
      if (existing) return existing.id;
      const created = await createFolder(name, parentId ?? null);
      return created.id;
    })();

    cache.set(key, promise);
    return promise;
  }

  return resolveOne;
}

/**
 * 依序解析一串路徑片段（例如 ["MyFolder", "sub"]），
 * 從 baseFolderId 開始，一層一層確保每個資料夾存在，回傳最底層的 folder id。
 */
export async function resolveFolderPath(resolveOne, pathSegments, baseFolderId) {
  let currentParent = baseFolderId ?? null;
  for (const segment of pathSegments) {
    currentParent = await resolveOne(segment, currentParent);
  }
  return currentParent;
}

/**
 * 從 <input type="file" webkitdirectory> 選出來的 FileList，
 * 轉成統一格式：[{ relativePath, file }]。
 * webkitRelativePath 長得像 "MyFolder/sub/photo.jpg"。
 */
export function collectFromInputFileList(fileList) {
  return Array.from(fileList).map((file) => ({
    relativePath: file.webkitRelativePath || file.name,
    file,
  }));
}

/**
 * 從拖曳事件的 DataTransferItemList 遞迴走訪，
 * 不管拖進來的是單一檔案、多個檔案、還是整個資料夾（含巢狀子資料夾），
 * 統一轉成 [{ relativePath, file }]。
 */
export function collectFromDataTransferItems(items) {
  const results = [];

  function readAllEntries(dirReader) {
    return new Promise((resolve, reject) => {
      const all = [];
      function readBatch() {
        // readEntries 每次最多回傳一批，讀到空陣列才代表真的讀完了，
        // 這是瀏覽器 API 的既有限制，要用迴圈讀到底。
        dirReader.readEntries((batch) => {
          if (batch.length === 0) {
            resolve(all);
          } else {
            all.push(...batch);
            readBatch();
          }
        }, reject);
      }
      readBatch();
    });
  }

  async function walk(entry, prefix) {
    if (entry.isFile) {
      const file = await new Promise((resolve, reject) => entry.file(resolve, reject));
      results.push({ relativePath: prefix + entry.name, file });
    } else if (entry.isDirectory) {
      const reader = entry.createReader();
      const children = await readAllEntries(reader);
      for (const child of children) {
        await walk(child, `${prefix}${entry.name}/`);
      }
    }
  }

  const topEntries = Array.from(items)
    .map((item) => item.webkitGetAsEntry())
    .filter(Boolean);

  return Promise.all(topEntries.map((entry) => walk(entry, ""))).then(() => results);
}