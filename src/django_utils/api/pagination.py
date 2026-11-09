from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

__all__ = [
    "StandardResultsSetPagination",
]


class StandardResultsSetPagination(PageNumberPagination):
    page_size_query_param = "page_size"
    max_page_size = 25

    def get_paginated_response(self, data):
        return Response(
            {
                "results": data,
                "pagination": {
                    "count": self.page.paginator.count,
                    "next": self.get_next_link(),
                    "previous": self.get_previous_link(),
                    "page_size": self.page.paginator.per_page,
                    "current_page": self.page.number,
                    "total_pages": self.page.paginator.num_pages,
                },
            }
        )
