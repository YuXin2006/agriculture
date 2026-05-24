def read_page_params(request, default_size=10):
    try:
        page = int(request.query_params.get("page", 1))
    except (TypeError, ValueError):
        page = 1
    try:
        page_size = int(request.query_params.get("page_size", default_size))
    except (TypeError, ValueError):
        page_size = default_size

    page = max(page, 1)
    page_size = max(min(page_size, 100), 1)
    return page, page_size


def paginate_queryset(queryset, page, page_size):
    total = queryset.count()
    total_pages = (total + page_size - 1) // page_size if total else 0
    offset = (page - 1) * page_size
    items = list(queryset[offset : offset + page_size])
    return items, {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
    }
