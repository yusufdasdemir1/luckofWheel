from django.core.paginator import Paginator
from rest_framework import status
from rest_framework.response import Response

DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 50


def int_param(request, name, default, minimum=1, maximum=None):
    try:
        value = int(request.query_params.get(name, default))
    except (TypeError, ValueError):
        return default
    value = max(minimum, value)
    return min(value, maximum) if maximum else value


def wants_page(request, extra_keys=()):
    """Sayfalama/filtre parametresi geldiyse sayfalı yanıt döner; gelmediyse eski düz liste korunur."""
    keys = ("page", "page_size", *extra_keys)
    return any(key in request.query_params for key in keys)


def paginated_response(request, queryset, serializer_class, extra=None, context=None):
    """count / page / page_size / total_pages / results (+ opsiyonel ekstra alanlar)."""
    page_size = int_param(request, "page_size", DEFAULT_PAGE_SIZE, 1, MAX_PAGE_SIZE)
    paginator = Paginator(queryset, page_size)
    page = paginator.get_page(int_param(request, "page", 1))  # taşan sayfa son sayfaya çekilir

    body = {
        "count": paginator.count,
        "page": page.number,
        "page_size": page_size,
        "total_pages": paginator.num_pages,
        "results": serializer_class(page.object_list, many=True, context=context or {}).data,
    }
    if extra:
        body.update(extra)

    return Response(body, status=status.HTTP_200_OK)
