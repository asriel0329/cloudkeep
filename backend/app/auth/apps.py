from django.apps import AppConfig


class AuthConfig(AppConfig):
    """
    注意：這個資料夾雖然叫 "auth"，但 app_label 故意設成 "accounts"。

    原因：Django 內建的 django.contrib.auth 這個套件，它的 app_label
    本身就叫 "auth"，如果我們不指定、讓 Django 自動用資料夾名稱當
    app_label，會直接撞名衝突（兩個 app 都想叫 "auth"）。
    所以這裡明確指定成 "accounts"，資料夾名稱維持 "auth" 不變，
    對外的 API 路徑、程式碼裡的模組路徑都還是 app.auth.xxx，
    只有 Django 內部用來識別 app 的 app_label 是 "accounts"。
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "app.auth"
    label = "accounts"
    verbose_name = "使用者帳號"
