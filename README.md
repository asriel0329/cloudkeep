# Cloud Drive

一個接近 Nextcloud 的 self-hosted 雲端硬碟專案。React 前端 + Django 後端，支援檔案上傳/下載、資料夾管理、分享連結與權限控制，儲存層可在 Local / S3 間切換。

## 架構

```
                         Internet / 瀏覽器
                                │
                                ▼
                         ┌─────────────┐
                         │    Nginx    │
                         │ TLS / Proxy │
                         │ Upload 設定  │
                         └──────┬──────┘
                                │
                ┌───────────────┴───────────────┐
                │                                │
                ▼                                ▼
        ┌───────────────┐               ┌────────────────┐
        │ React 靜態檔    │               │     /api/*      │
        │ (SPA build)    │               │                 │
        └───────────────┘               ▼
                                  ┌─────────────┐
                                  │   Django    │
                                  └──────┬──────┘
                                         │
                ┌────────────┬───────────┼────────────┐
                ▼            ▼           ▼            ▼
            ┌───────┐   ┌─────────┐  ┌───────┐  ┌────────────┐
            │ Auth  │   │File API │  │ Share │  │ Permission │
            └───────┘   └─────────┘  └───────┘  └────────────┘
                │            │           │            │
                └────────────┴─────┬─────┴────────────┘
                                    │
                ┌───────────────────┼───────────────────┐
                ▼                   ▼                   ▼
        ┌───────────────┐   ┌─────────────┐    ┌─────────────────┐
        │  PostgreSQL   │   │    Redis    │    │ Storage Service │
        │               │   │             │    │  (抽象介面)      │
        │ users         │   │ Celery      │    │ save/read/delete│
        │ files         │   │  broker     │    └────────┬────────┘
        │ folders       │   │ cache(後期) │             │
        │ shares        │   └──────┬──────┘    ┌────────┴────────┐
        │ permissions   │          │           ▼                 ▼
        │ (hash,        │          ▼      ┌──────────┐    ┌──────────┐
        │  storage_key) │   ┌─────────────┐│  Local   │    │    S3    │
        └───────────────┘   │Celery Worker││ Storage  │    │  Storage │
                             │             │└──────────┘    └──────────┘
                             │ 縮圖產生     │
                             │ 病毒掃描     │
                             │ checksum    │
                             │ metadata    │
                             └─────────────┘
```

### 設計原則

1. Nginx 是「分流」不是「必經路徑」——靜態檔案直接吐給瀏覽器，只有 `/api/*` 才進 Django
2. Permission 掛在 `folder_id` 上、往下繼承，不同時掛在檔案與資料夾
3. `files` 表的 `hash`（SHA-256）、`storage_key` 欄位從 Phase 1 就先留好，方便後期做去重
4. Celery 只處理「不需要立即完成」的任務（縮圖、掃毒、checksum），一般上傳/下載不進佇列
5. Storage Service 抽象層讓 Local → S3 的搬遷不用動上層邏輯

## 技術棧

| 層級 | 技術 |
|---|---|
| 前端 | React |
| 反向代理 | Nginx |
| 後端 | Django + Django REST Framework |
| 資料庫 | PostgreSQL |
| 佇列/快取 | Redis + Celery |
| 儲存 | Local Storage / S3 相容（MinIO） |
| 容器化 | Docker Compose |

## 開發階段規劃

- [ ] **Phase 1** — 基礎功能：註冊/登入、上傳/下載/刪除、資料夾、PostgreSQL、Local Storage、Docker Compose
- [ ] **Phase 2** — 權限：分享連結、Permission、到期時間、密碼保護分享
- [ ] **Phase 3** — Infrastructure：Nginx 正式設定、HTTPS、Celery、Redis、背景任務
- [ ] **Phase 4** — Storage 抽象化：S3Storage、MinIO 整合
- [ ] **Phase 5** — 進階功能：Chunked/Resumable Upload、檔案版本控制、回收桶、去重偵測、儲存配額、Audit Log

## 本機開發

```bash
docker compose up -d
```

## 目錄結構

```
cloud-drive/
├── backend/            # Django 專案
│   └── app/
│       ├── auth/       # 認證模組
│       ├── files/      # 檔案 API
│       ├── folders/    # 資料夾管理
│       ├── shares/     # 分享連結
│       ├── permissions/# 權限控制
│       └── storage/    # Storage 抽象層 (Local / S3)
├── frontend/           # React 專案
├── docker/             # Dockerfile 等容器設定
├── docker-compose.yml
└── .env.example
```

## License

TBD
