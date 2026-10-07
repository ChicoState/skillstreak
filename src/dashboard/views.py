"""Views for the authenticated sample dashboard."""

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


@login_required
def preview(request: HttpRequest) -> HttpResponse:
    """Render the static dashboard for the authenticated user."""
    return render(request, "dashboard/preview.html")
