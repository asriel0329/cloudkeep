from django.contrib.auth import authenticate, get_user_model, login, logout
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import LoginSerializer, RegisterSerializer, UserSerializer

User = get_user_model()


class RegisterView(APIView):
    """
    POST /api/auth/register/
    body: { "username": "...", "email": "...", "password": "..." }
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # 註冊完直接幫使用者登入，體驗上比較順（不用註冊完再登入一次）
        login(request, user)

        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """
    POST /api/auth/login/
    body: { "username": "...", "password": "..." }

    這裡用的是 Django 內建的 session-based 登入機制：
    登入成功後，Django 會在回應裡設定一個 session cookie，
    之後瀏覽器每次打 API 都會自動帶著這個 cookie，
    後端就知道「這是誰在打 API」，不需要每次都重新傳帳密。
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            request,
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"],
        )

        if user is None:
            return Response(
                {"detail": "帳號或密碼錯誤"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        login(request, user)
        return Response(UserSerializer(user).data)


class LogoutView(APIView):
    """POST /api/auth/logout/ —— 需要先登入才能呼叫"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    """GET /api/auth/me/ —— 取得目前登入使用者的資料，用來確認登入狀態"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)
