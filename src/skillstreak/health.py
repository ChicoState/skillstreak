"""Liveness endpoint for container orchestration."""

from django.http import JsonResponse
from django.http.request import HttpRequest


def health_check(_: HttpRequest) -> JsonResponse:
    """Return a constant liveness response without querying dependencies."""
    return JsonResponse({"status": "ok"})
