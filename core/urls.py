from django.urls import path

from core.views.company_views.login_view import LoginView
from core.views.company_views.register_view import RegisterView
from core.views.company_views.logout_view import LogoutView
from core.views.company_views.spin_history_view import CompanySpinHistoryView
from core.views.company_views.update_company_view import CompanyUpdateView
from core.views.company_views.update_is_used_view import EarnedWinStatusUpdateView
from core.views.company_views.my_information_view import MeView
from core.views.company_views.earned_wins_delete import EarnedWinsDeleteView


from core.views.public_views.public_register_view import PublicRegisterView
from core.views.public_views.public_show_services_view import PublicServiceListView
from core.views.public_views.public_show_gifts import PublicGiftView
from core.views.public_views.public_show_available_meetings import PublicOccupiedMeetingsView
from core.views.public_views.public_show_companies import ShowCompaniesView
from core.views.public_views.public_show_company_detail import PublicCompanyDetailView


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
from core.views.meeting_views.meeting_list_view import MeetingListView
from core.views.meeting_views.meeting_update_view import MeetingUpdateView
from core.views.meeting_views.meeting_get_view import MeetingDetailView
from core.views.meeting_views.meeting_delete_view import MeetingDeleteView
from core.views.meeting_views.meeting_update_is_status import MeetingCancelView
from core.views.meeting_views.meeting_statistic_view import MeetingStatisticsView


from rest_framework_simplejwt.views import TokenRefreshView
from core.views.token_views.get_admin_token import AdminTokenObtainPairView
urlpatterns = [
    path("api/token", AdminTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh", TokenRefreshView.as_view(), name="token_refresh"),
    path('company/login', LoginView.as_view(), name='login'),
    path('company/register', RegisterView.as_view(), name='register'),
    path("public/register/<slug:slug>", PublicRegisterView.as_view(), name="public_views"),
    path("company/gifts/create", GiftCreateView.as_view(), name="gift_create"),
    path("spin_history", CompanySpinHistoryView.as_view(), name="company_spin_history"),
    path("companies/<slug:company_slug>", CompanyUpdateView.as_view(), name="company-update"),
    path("company/earned-wins/status/<int:earned_win_id>", EarnedWinStatusUpdateView.as_view(), name="company_is_used"),
    path("company/gifts/list", GiftListView.as_view(), name="gift_list"),
    path("company/gift/delete/<int:gift_id>", GiftDeleteView.as_view(), name="gift_delete"),
    path("company/gifts/delete-all", GiftDeleteAllView.as_view(), name="gift_delete_all"),
    path("company/gift/update/<int:gift_id>", GiftUpdateView.as_view(), name="gift_update"),
    path("company/gift/detail/<int:gift_id>", GiftDetailView.as_view(), name="gift_detail"),
    path("company/services/create", ServiceCreateView.as_view(), name="service-create"),
    path("company/services/list", ServiceListView.as_view(), name="service-list"),
    path("company/services/update/<int:service_id>", ServiceUpdateView.as_view(), name="service-update"),
    path("company/services/delete/<int:service_id>", ServiceDeleteView.as_view(), name="service_delete"),
    path("company/services/delete-all", ServiceDeleteAllView.as_view(), name="service_delete_all"),
    path("company/services/<int:service_id>",ServiceDetailView.as_view(), name="service_detail"),
    path("company/services/filter", ServiceFilterView.as_view(), name="service-filter"),
    path("public/services/<slug:slug>", PublicServiceListView.as_view(), name="public-services"),
    path("public/meeting/create/<slug:company_slug>", MeetingCreateView.as_view(), name="meeting-create"),
    path("company/meeting/list", MeetingListView.as_view(), name="meeting-list"),
    path("company/meetings/update/<int:meeting_id>", MeetingUpdateView.as_view(), name="meeting-update"),
    path("company/meetings/detail/<int:meeting_id>", MeetingDetailView.as_view(), name="meeting-detail"),
    path("company/meetings/delete/<int:meeting_id>", MeetingDeleteView.as_view(), name="meeting-delete"),
    path("company/meetings/cancel/<int:meeting_id>", MeetingCancelView.as_view(), name="meeting-cancel"),
    path("meetings/statistics", MeetingStatisticsView.as_view(), name="meeting-statistics"),
    path("public/gifts/<slug:slug>", PublicGiftView.as_view(), name="public_gift_list"),
    path("company/logout", LogoutView.as_view(), name="logout"),
    path("public/occupied-meetings/<slug>",PublicOccupiedMeetingsView.as_view(), name="public-occupied-meetings"),
    path("public/companies", ShowCompaniesView.as_view(), name="show_companies"),
    path("company/me", MeView.as_view(), name="me"),
    path("public/companies/<slug:slug>", PublicCompanyDetailView.as_view(), name="show_companies"),
    path("company/earned-wins/<int:earned_wins_id>",EarnedWinsDeleteView.as_view(), name="earned_wins_delete"),
]
