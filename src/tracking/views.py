"""Protected skill selection and binary completion actions."""

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import DailyCompletion, Skill, UserSkill


@login_required
@require_POST
def toggle_selection(request: HttpRequest, skill_id: int) -> HttpResponse:
    skill = get_object_or_404(
        Skill, pk=skill_id, visibility=Skill.Visibility.SYSTEM, is_active=True
    )
    user_skill, created = UserSkill.objects.get_or_create(
        user=request.user,
        skill=skill,
        defaults={"started_on": timezone.localdate(), "is_active": True},
    )
    if not created:
        user_skill.is_active = not user_skill.is_active
        user_skill.save(update_fields=["is_active"])
    return redirect("dashboard-preview")


@login_required
@require_POST
def toggle_completion(request: HttpRequest, user_skill_id: int) -> HttpResponse:
    user_skill = get_object_or_404(UserSkill, pk=user_skill_id, user=request.user, is_active=True)
    completion, created = DailyCompletion.objects.get_or_create(
        user_skill=user_skill, completed_on=timezone.localdate()
    )
    if not created:
        completion.delete()
    return redirect("dashboard-preview")
