from django.urls import path
from core.views.auth_view.login_view import LoginView
from core.views.auth_view.register_view import RegisterView
from core.views.public_register.client_view import PublicRegisterView
from core.views.gift.gift_create_view import GiftCreateView
urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path("public/register/<slug:slug>/", PublicRegisterView.as_view(), name="public_register"),
    path("gift/create/", GiftCreateView.as_view(), name="gift_create"),
]
