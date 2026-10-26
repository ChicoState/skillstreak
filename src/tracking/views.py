"""Protected skill selection, creation, and binary completion actions."""

from uuid import uuid4

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from .forms import CustomSkillForm
from .models import DailyCompletion, MissedSkillEpisode, Skill, UserSkill, UserSkillSchedule


@login_required
@require_http_methods(["GET", "POST"])
def create_custom_skill(request: HttpRequest) -> HttpResponse:
    """Create an active private skill and its current recurring goal."""
    form = CustomSkillForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            skill = Skill.objects.create(
                slug=f"private-{uuid4().hex}",
                name=form.cleaned_data["name"],
                description=form.cleaned_data["description"],
                visibility=Skill.Visibility.PRIVATE,
                created_by=request.user,
            )
            user_skill = UserSkill.objects.create(
                user=request.user,
                skill=skill,
                started_on=form.cleaned_data["started_on"],
            )
            frequency = form.cleaned_data["frequency"]
            schedule_data = {
                "user_skill": user_skill,
                "effective_from": user_skill.started_on,
            }
            if frequency == CustomSkillForm.Frequency.DAILY:
                schedule_data["rule_type"] = UserSkillSchedule.RuleType.DAILY
            elif frequency == CustomSkillForm.Frequency.WEEKLY:
                schedule_data.update(
                    rule_type=UserSkillSchedule.RuleType.DAYS_PER_WEEK,
                    target_days_per_week=form.cleaned_data["target_days"],
                    week_starts_on=1,
                )
            else:
                schedule_data.update(
                    rule_type=UserSkillSchedule.RuleType.DAYS_PER_MONTH,
                    target_days_per_month=form.cleaned_data["target_days"],
                )
            UserSkillSchedule.objects.create(**schedule_data)
        return redirect("dashboard-preview")
    return render(request, "tracking/create_skill.html", {"form": form})


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
    with transaction.atomic():
        completion, created = DailyCompletion.objects.get_or_create(
            user_skill=user_skill, completed_on=timezone.localdate()
        )
        if created:
            MissedSkillEpisode.objects.filter(
                user_skill=user_skill,
                closed_at__isnull=True,
            ).update(closed_at=timezone.now())
        else:
            completion.delete()
    return redirect("dashboard-preview")
