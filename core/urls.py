from django.urls import path
from core.views.company_views.login_view import LoginView
from core.views.company_views.register_view import RegisterView
from core.views.public_views.public_register_view import PublicRegisterView
from core.views.gift_views.gift_create_view import GiftCreateView
from core.views.company_views.spin_history_view import CompanySpinHistoryView
from core.views.company_views.update_company_view import CompanyUpdateView
from core.views.company_views.update_is_used_view import EarnedWinStatusUpdateView
from core.views.gift_views.gift_list_view import GiftListView
from core.views.gift_views.gift_delete_view import GiftDeleteView
from core.views.gift_views.gift_delete_all_view import GiftDeleteAllView
from core.views.gift_views.gift_update_view import GiftUpdateView
from core.views.gift_views.gift_get_view import GiftDetailView

urlpatterns = [
    path('company/login/', LoginView.as_view(), name='login'),
    path('company/register/', RegisterView.as_view(), name='register'),
    path("public/register/<slug:slug>/", PublicRegisterView.as_view(), name="public_views"),
    path("company/gifts/create/", GiftCreateView.as_view(), name="gift_create"),
    path("spin_history/", CompanySpinHistoryView.as_view(), name="company_spin_history"),
    path("companies/<slug:company_slug>/", CompanyUpdateView.as_view(), name="company-update"),

    path("company/earned-wins/status/<int:earned_win_id>/", EarnedWinStatusUpdateView.as_view(), name="company_is_used"),
    path("company/gifts/list/", GiftListView.as_view(), name="gift_list"),
    path("company/gift/delete/<int:gift_id>", GiftDeleteView.as_view(), name="gift_delete"),
    path("company/gifts/delete-all/", GiftDeleteAllView.as_view(), name="gift_delete_all"),
    path("company/gift/update/<int:gift_id>/", GiftUpdateView.as_view(), name="gift_update"),
    path("company/gift/detail/<int:gift_id>", GiftDetailView.as_view(), name="gift_detail"),

]
