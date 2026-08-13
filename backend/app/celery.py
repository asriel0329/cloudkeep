import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")

app = Celery("app")

# 讀取 Django settings.py 裡所有 CELERY_ 開頭的設定
app.config_from_object("django.conf:settings", namespace="CELERY")

# 自動掃描每個 INSTALLED_APPS 底下的 tasks.py，之後 P3-3
# 你只要在 app/files/tasks.py 寫 @app.task 的函式，這裡完全不用改
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")