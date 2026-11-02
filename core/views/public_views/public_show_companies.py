from django.core.paginator import Paginator
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Companies
from core.serializers.public_serializers.public_serializers import ShowCompaniesSerializer

DEFAULT_PAGE_SIZE = 8
MAX_PAGE_SIZE = 24
FILTER_PARAMS = ("page", "page_size", "city", "district", "q")


def _norm(value):
    """Türkçe harflere duyarlı, büyük/küçük harften bağımsız karşılaştırma anahtarı."""
    return (value or "").strip().replace("İ", "i").replace("I", "ı").lower()


def _tr_title(value):
    """'nilüfer' -> 'Nilüfer', 'istanbul' -> 'İstanbul' (Türkçe i/ı kurallarıyla)."""
    words = []
    for word in (value or "").strip().split():
        lowered = word.replace("İ", "i").replace("I", "ı").lower()
        first = {"i": "İ", "ı": "I"}.get(lowered[0], lowered[0].upper())
        words.append(first + lowered[1:])
    return " ".join(words)


def _int_param(request, name, default, minimum=1, maximum=None):
    try:
        value = int(request.query_params.get(name, default))
    except (TypeError, ValueError):
        return default
    value = max(minimum, value)
    return min(value, maximum) if maximum else value


def _matching_raw_values(queryset, field, wanted):
    """Veritabanındaki yazımı ne olursa olsun ('istanbul', 'İstanbul') eşleşen ham değerler."""
    wanted_key = _norm(wanted)
    raw = queryset.exclude(**{field: ""}).values_list(field, flat=True).distinct()
    return [value for value in raw if _norm(value) == wanted_key]


def _build_filters(active_companies):
    """Filtre kutuları için: aktif salonlardaki şehirler ve her şehrin ilçeleri."""
    grouped = {}
    pairs = active_companies.exclude(city="").values_list("city", "district").distinct()
    for city, district in pairs:
        entry = grouped.setdefault(_norm(city), {"city": _tr_title(city), "districts": {}})
        if district and district.strip():
            entry["districts"].setdefault(_norm(district), _tr_title(district))

    return [
        {"city": entry["city"], "districts": sorted(entry["districts"].values(), key=_norm)}
        for entry in sorted(grouped.values(), key=lambda e: _norm(e["city"]))
    ]


class ShowCompaniesView(APIView):
    @swagger_auto_schema(
        operation_summary="🏢 Public: Aktif salonları listele (sayfalı, filtreli)",
        operation_description=(
            "Hiç parametre verilmezse eski davranış korunur: tüm aktif salonlar düz liste olarak döner.\n\n"
            "`page`, `page_size`, `city`, `district` veya `q` verilirse sayfalı yanıt döner: "
            "`count`, `page`, `page_size`, `total_pages`, `results` ve filtre kutuları için `filters`."
        ),
        manual_parameters=[
            openapi.Parameter("page", openapi.IN_QUERY, description="Sayfa numarası (varsayılan 1)", type=openapi.TYPE_INTEGER),
            openapi.Parameter(
                "page_size",
                openapi.IN_QUERY,
                description=f"Sayfa başına salon (varsayılan {DEFAULT_PAGE_SIZE}, en fazla {MAX_PAGE_SIZE})",
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter("city", openapi.IN_QUERY, description="Şehir (büyük/küçük harften bağımsız)", type=openapi.TYPE_STRING),
            openapi.Parameter("district", openapi.IN_QUERY, description="İlçe (büyük/küçük harften bağımsız)", type=openapi.TYPE_STRING),
            openapi.Parameter("q", openapi.IN_QUERY, description="Salon adında arama", type=openapi.TYPE_STRING),
        ],
        tags=["PUBLIC"],
    )
    def get(self, request):
        active = Companies.objects.filter(status="active")
        params = request.query_params

        # eski istemciler: parametre yoksa düz liste (geriye dönük uyumluluk)
        if not any(key in params for key in FILTER_PARAMS):
            serializer = ShowCompaniesSerializer(active, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        queryset = active

        city = params.get("city", "").strip()
        if city:
            queryset = queryset.filter(city__in=_matching_raw_values(active, "city", city))

        district = params.get("district", "").strip()
        if district:
            queryset = queryset.filter(district__in=_matching_raw_values(active, "district", district))

        query = params.get("q", "").strip()
        if query:
            queryset = queryset.filter(title__icontains=query)

        queryset = queryset.order_by("id")

        page_size = _int_param(request, "page_size", DEFAULT_PAGE_SIZE, 1, MAX_PAGE_SIZE)
        paginator = Paginator(queryset, page_size)
        page = paginator.get_page(_int_param(request, "page", 1))  # taşan sayfa son sayfaya çekilir

        return Response(
            {
                "count": paginator.count,
                "page": page.number,
                "page_size": page_size,
                "total_pages": paginator.num_pages,
                "results": ShowCompaniesSerializer(page.object_list, many=True).data,
                "filters": {"cities": _build_filters(active)},
            },
            status=status.HTTP_200_OK,
        )
