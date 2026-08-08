from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """
    註冊用的序列化器。

    password 欄位設成 write_only，代表這個欄位只接受「寫入」
    （前端傳密碼進來），但序列化「輸出」使用者資料時（例如
    GET /api/auth/me/）絕對不會把密碼欄位吐回去，避免密碼外洩。
    """

    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password"]

    def create(self, validated_data):
        # 一定要用 create_user()，不能用 create()，
        # 因為 create_user() 會自動把密碼雜湊(hash)過再存進資料庫，
        # 用一般的 create() 密碼會變成明文存進去，是嚴重的安全問題。
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
        )
        return user


class UserSerializer(serializers.ModelSerializer):
    """用於回傳「目前登入使用者」的基本資料，不含密碼欄位。"""

    class Meta:
        model = User
        fields = ["id", "username", "email", "storage_quota_bytes", "date_joined"]


class LoginSerializer(serializers.Serializer):
    """登入用，只是單純驗證有沒有傳 username/password，不對應到 model。"""

    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
