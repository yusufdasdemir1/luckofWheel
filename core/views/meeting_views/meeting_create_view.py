from datetime import datetime, timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from core.models import Companies, Users, Meetings, Services, MailTemplate, Staff
from core.serializers.public_serializers.public_serializers import PublicMeetingCreateSerializer
from core.models import EarnedWins
from core.services.mail_service import MailService
from core.services.spin import spin_status
from core.services.working_hours import hours_for_day, salon_now
from django.conf import settings
from django.db import transaction


class MeetingCreateView(APIView):
    @swagger_auto_schema(
        operation_summary="🗓️ Public: Randevu oluştur (slug bazlı, hizmet süresiyle)",
        operation_description=(
            "Müşteri, firma slug'ına göre randevu oluşturur.\n\n"
            "Hizmet süresi `Services` tablosundan otomatik alınır.\n"
            "Randevu bitiş saati (end_time) otomatik hesaplanır.\n\n"
            "Firmanın aktif çalışanı (kuaför) varsa `staff_id` zorunludur ve çakışma kontrolü "
            "o çalışanın takvimine göre yapılır. Randevu firmanın çalışma saatleri içinde olmalıdır."
        ),
        request_body=PublicMeetingCreateSerializer,
        responses={
            201: "Randevu oluşturuldu",
            400: "Geçersiz veri, çalışma saatleri dışında, geçmiş saat veya zaman çakışması var",
            404: "Firma, kullanıcı veya hizmet bulunamadı",
        },
        tags=["MEETINGS"],
    )
    def post(self, request, company_slug):
        # 1️⃣ Firma kontrolü
        try:
            company = Companies.objects.get(slug=company_slug)
        except Companies.DoesNotExist:
            return Response({"error": "Firma bulunamadı."}, status=status.HTTP_404_NOT_FOUND)

        serializer = PublicMeetingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone=serializer.validated_data["phone"]
        service_title=serializer.validated_data["service_title"]
        date=serializer.validated_data["date"]
        time=serializer.validated_data["time"]
        note=serializer.validated_data.get("note", "")
        staff_id=serializer.validated_data.get("staff_id")

        try:
            user = Users.objects.get(phone=phone, company=company)
        except Users.DoesNotExist:
            return Response(
                {"error": "Bu telefon numarasına ait kullanıcı bulunamadı."},
                status=status.HTTP_404_NOT_FOUND
            )

        # 2️⃣ Çalışan (kuaför) seçimi: firmanın aktif çalışanı varsa zorunlu
        active_staff = Staff.objects.filter(company=company, is_active=True).select_related("user")
        staff = None
        if active_staff.exists():
            if not staff_id:
                return Response(
                    {"error": "Lütfen bir kuaför seçin."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            staff = active_staff.filter(id=staff_id).first()
            if not staff:
                return Response(
                    {"error": "Seçilen kuaför bulunamadı veya aktif değil."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # 3️⃣ Hizmet kontrolü
        try:
            service = Services.objects.get(company=company, title=service_title, is_active=True)
        except Services.DoesNotExist:
            return Response(
                {"error": "Seçilen hizmet bulunamadı veya pasif durumda."},
                status=status.HTTP_404_NOT_FOUND
            )

        start_datetime = datetime.combine(date, time)
        end_datetime = start_datetime + timedelta(minutes=service.duration)
        end_time = end_datetime.time()

        # 4️⃣ Geçmiş saat ve çalışma saatleri kontrolü (salonun yerel saatine göre)
        if start_datetime <= salon_now():
            return Response(
                {"error": "Geçmiş bir saat için randevu alınamaz."},
                status=status.HTTP_400_BAD_REQUEST
            )

        day_hours = hours_for_day(company, date.weekday())
        if day_hours["is_closed"]:
            return Response(
                {"error": "Salon seçilen gün kapalıdır."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if time < day_hours["opens"] or end_datetime > datetime.combine(date, day_hours["closes"]):
            return Response(
                {"error": "Seçilen saat salonun çalışma saatleri dışında."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 5️⃣ Çakışma kontrolü: çalışan seçildiyse sadece o çalışanın takvimi
        overlap = Meetings.objects.filter(
            company=company,
            date=date,
            time__lt=end_time,
            end_time__gt=time,
            status__in=["waiting","arrived"]
        )
        if staff:
            overlap = overlap.filter(staff=staff)

        if overlap.exists():
            return Response(
                {"error": "Bu saat aralığında başka bir randevu zaten mevcut."},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            meeting=Meetings.objects.create(
                user=user,
                company=company,
                staff=staff,
                service_title=service.title,
                service_duration=service.duration,
                service_price=service.price,
                date=date,
                time=time,
                end_time=end_time,
                note=note
            )

            # Çark randevudan önceyse az önce çevrilen (bağsız) son hediye bu randevuya bağlanır
            earned_gift = None
            if company.wheel_mode == Companies.WHEEL_BEFORE:
                earned_gift = EarnedWins.objects.filter(
                    user=user,
                    company=company,
                    is_used=False,
                    meeting__isnull=True
                ).order_by("-created_at").first()
                if earned_gift:
                    earned_gift.meeting = meeting
                    earned_gift.save(update_fields=["meeting", "updated_at"])

        staff_name = f"{staff.user.name} {staff.user.surname}".strip() if staff else "-"

        transaction.on_commit(lambda: MailService.send_async(
            company=company,
            key=MailTemplate.APPOINTMENT_CREATED,
            to_email=user.email,
            context_data={
                "user_name": user.name,
                "company_name": company.title,
                "meeting_date": meeting.date.strftime("%d.%m.%Y"),
                "meeting_time": meeting.time.strftime("%H:%M"),
                "gift_title": earned_gift.gift_title if earned_gift else "-",
                "company_phone": company.phone,
                "service_title": meeting.service_title,
                "staff_name": staff_name,
                "review_url": f"{settings.FRONTEND_URL}/{company.slug}/degerlendir/{meeting.review_token}",
            }
        ))

        return Response(
            {
                "meeting_id": meeting.id,
                "wheel_mode": company.wheel_mode,
                # çark randevudan sonraysa ön yüz çark adımında hakkı buradan gösterir
                **spin_status(user, company),
                "message": f"Randevunuz oluşturuldu: {service.title} ({date} {time} - {end_time})",
                "duration": f"{service.duration} dakika",
                "price": f"{service.price} ₺",
                "staff": staff_name,
                "note": f"{note}",
            },
            status=status.HTTP_201_CREATED
        )
