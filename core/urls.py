from django.urls import path
from core.views.company_views.login_view import LoginView
from core.views.company_views.register_view import RegisterView
from core.views.public_views.public_register_view import PublicRegisterView
from core.views.gift_views.gift_create_view import GiftCreateView
from core.views.company_views.spin_history_view import CompanySpinHistoryView
from core.views.company_views.update_company_view import CompanyUpdateView
urlpatterns = [
    path('company/login/', LoginView.as_view(), name='login'),
    path('company/register/', RegisterView.as_view(), name='register'),
    path("public/register/<slug:slug>/", PublicRegisterView.as_view(), name="public_views"),
    path("gift_views/create/", GiftCreateView.as_view(), name="gift_create"),
    path("spin_history/", CompanySpinHistoryView.as_view(), name="company_spin_history"),
    path("companies/<slug:company_slug>/", CompanyUpdateView.as_view(), name="company-update"),
]
