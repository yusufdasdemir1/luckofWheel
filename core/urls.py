from django.urls import path

from core.views.company_views.login_view import LoginView
from core.views.company_views.register_view import RegisterView

from core.views.public_views.public_register_view import PublicRegisterView
from core.views.public_views.public_show_services_view import PublicServiceListView

from core.views.company_views.spin_history_view import CompanySpinHistoryView
from core.views.company_views.update_company_view import CompanyUpdateView
from core.views.company_views.update_is_used_view import EarnedWinStatusUpdateView

from core.views.gift_views.gift_list_view import GiftListView
from core.views.gift_views.gift_delete_view import GiftDeleteView
from core.views.gift_views.gift_delete_all_view import GiftDeleteAllView
from core.views.gift_views.gift_update_view import GiftUpdateView
from core.views.gift_views.gift_get_view import GiftDetailView
from core.views.gift_views.gift_create_view import GiftCreateView

from core.views.service_views.service_create_view import ServiceCreateView
from core.views.service_views.service_list_view import ServiceListView
from core.views.service_views.service_update_view import ServiceUpdateView
from core.views.service_views.service_delete_view import ServiceDeleteView
from core.views.service_views.service_delete_all_view import ServiceDeleteAllView
from core.views.service_views.service_get_view import ServiceDetailView
from core.views.service_views.service_filter_view import ServiceFilterView

from core.views.meeting_views.meeting_create_view import MeetingCreateView


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
    path("services/create/", ServiceCreateView.as_view(), name="service-create"),
    path("services/list/", ServiceListView.as_view(), name="service-list"),
    path("services/update/<int:service_id>/", ServiceUpdateView.as_view(), name="service-update"),
    path("services/delete/<int:service_id>/", ServiceDeleteView.as_view(), name="service_delete"),
    path("services/delete-all/", ServiceDeleteAllView.as_view(), name="service_delete_all"),
    path("services/<int:service_id>/",ServiceDetailView.as_view(), name="service_detail"),
    path("services/filter/", ServiceFilterView.as_view(), name="service-filter"),
    path("public/services/<slug:slug>/", PublicServiceListView.as_view(), name="public-services"),
    path("public/meeting/create/<slug:company_slug>/", MeetingCreateView.as_view(), name="meeting-create"),
]
