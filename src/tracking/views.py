"""Protected skill selection, creation, and binary completion actions."""

from urllib.parse import urlencode
from uuid import uuid4

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from .forms import CustomSkillForm
from .library import archived_private_skills, available_library_skills, normalize_library_query
from .models import (
    DailyCompletion,
    MissedSkillEpisode,
    Skill,
    SkillTag,
    Tag,
    UserSkill,
    UserSkillSchedule,
)
from .tags import tag_slugs_for_text


def redirect_to_preview(
    request: HttpRequest,
    selected_user_skill_id: int | None = None,
    *,
    return_to_library: bool = False,
) -> HttpResponse:
    """Return to a validated dashboard view after a selection change."""
    parameters: dict[str, str] = {}
    if return_to_library:
        parameters["view"] = "library"
        query = normalize_library_query(request.POST.get("q", ""))
        tag_slug = request.POST.get("tag", "").strip()[:48]
        if query:
            parameters["q"] = query
        if Tag.objects.filter(slug=tag_slug).exists():
            parameters["tag"] = tag_slug
    if selected_user_skill_id is not None:
        parameters["skill"] = str(selected_user_skill_id)
    destination = reverse("dashboard-preview")
    if parameters:
        destination = f"{destination}?{urlencode(parameters)}"
    return redirect(destination)


def posted_active_user_skill_id(request: HttpRequest) -> int | None:
    """Return a posted selection only when it is active and belongs to the member."""
    selected_id = request.POST.get("skill", "")
    if not selected_id.isdecimal():
        return None
    active_selection = (
        UserSkill.objects.filter(pk=int(selected_id), user=request.user, is_active=True)
        .only("pk")
        .first()
    )
    return active_selection.pk if active_selection else None


def _private_skill_for_owner(request: HttpRequest, skill_id: int) -> Skill:
    return get_object_or_404(
        available_library_skills(request.user),
        pk=skill_id,
        visibility=Skill.Visibility.PRIVATE,
        created_by=request.user,
    )


def _schedule_form_initial(user_skill: UserSkill) -> dict[str, object]:
    schedule = user_skill.userskillschedule_set.order_by("-effective_from", "-pk").first()
    if schedule is None:
        return {"frequency": CustomSkillForm.Frequency.DAILY, "target_days": None}
    if schedule.rule_type == UserSkillSchedule.RuleType.DAYS_PER_WEEK:
        return {
            "frequency": CustomSkillForm.Frequency.WEEKLY,
            "target_days": schedule.target_days_per_week,
        }
    if schedule.rule_type == UserSkillSchedule.RuleType.DAYS_PER_MONTH:
        return {
            "frequency": CustomSkillForm.Frequency.MONTHLY,
            "target_days": schedule.target_days_per_month,
        }
    return {"frequency": CustomSkillForm.Frequency.DAILY, "target_days": None}


def _apply_schedule_goal(schedule: UserSkillSchedule, form: CustomSkillForm) -> None:
    schedule.rule_type = UserSkillSchedule.RuleType.DAILY
    schedule.interval_days = None
    schedule.target_days_per_week = None
    schedule.target_days_per_month = None
    schedule.week_starts_on = None
    schedule.short_month_policy = None
    frequency = form.cleaned_data["frequency"]
    if frequency == CustomSkillForm.Frequency.WEEKLY:
        schedule.rule_type = UserSkillSchedule.RuleType.DAYS_PER_WEEK
        schedule.target_days_per_week = form.cleaned_data["target_days"]
        schedule.week_starts_on = 1
    elif frequency == CustomSkillForm.Frequency.MONTHLY:
        schedule.rule_type = UserSkillSchedule.RuleType.DAYS_PER_MONTH
        schedule.target_days_per_month = form.cleaned_data["target_days"]


def _refresh_private_skill_tag(skill: Skill) -> None:
    matching_slugs = tag_slugs_for_text(skill.name, skill.description, limit=99)
    tags_by_slug = Tag.objects.in_bulk(matching_slugs, field_name="slug")
    matching_tag = next(
        (tags_by_slug[slug] for slug in matching_slugs if slug in tags_by_slug), None
    )
    SkillTag.objects.filter(skill=skill).delete()
    if matching_tag is not None:
        SkillTag.objects.create(skill=skill, tag=matching_tag)


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
            _refresh_private_skill_tag(skill)
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
        return redirect(f"{reverse('dashboard-preview')}?skill={user_skill.id}")
    return render(request, "tracking/create_skill.html", {"form": form})


@login_required
@require_http_methods(["GET", "POST"])
def edit_custom_skill(request: HttpRequest, skill_id: int) -> HttpResponse:
    """Edit an active private skill owned by the signed-in member."""
    skill = _private_skill_for_owner(request, skill_id)
    user_skill = get_object_or_404(UserSkill, user=request.user, skill=skill)
    initial = {
        "name": skill.name,
        "description": skill.description,
        **_schedule_form_initial(user_skill),
    }
    form = CustomSkillForm(request.POST or None, initial=initial, editing=True)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            skill.name = form.cleaned_data["name"]
            skill.description = form.cleaned_data["description"]
            skill.save(update_fields=["name", "description"])
            _refresh_private_skill_tag(skill)
            schedule = get_object_or_404(
                UserSkillSchedule,
                user_skill=user_skill,
                effective_through__isnull=True,
            )
            _apply_schedule_goal(schedule, form)
            schedule.save()
        return redirect(f"{reverse('dashboard-preview')}?skill={user_skill.id}")
    return render(
        request,
        "tracking/create_skill.html",
        {"form": form, "editing": True, "skill_id": skill.id},
    )


@login_required
@require_POST
def delete_custom_skill(request: HttpRequest, skill_id: int) -> HttpResponse:
    """Archive an owned private skill while retaining its history."""
    skill = _private_skill_for_owner(request, skill_id)
    with transaction.atomic():
        skill.archived_at = timezone.now()
        skill.save(update_fields=["archived_at"])
        UserSkill.objects.filter(user=request.user, skill=skill).update(is_active=False)
    return redirect(f"{reverse('dashboard-preview')}?view=library")


@login_required
@require_POST
def restore_custom_skill(request: HttpRequest, skill_id: int) -> HttpResponse:
    """Restore an archived private skill to the library, without selecting it."""
    skill = get_object_or_404(archived_private_skills(request.user), pk=skill_id)
    skill.archived_at = None
    skill.save(update_fields=["archived_at"])
    return redirect(f"{reverse('dashboard-preview')}?view=library")


@login_required
@require_POST
def toggle_selection(request: HttpRequest, skill_id: int) -> HttpResponse:
    skill = get_object_or_404(
        available_library_skills(request.user),
        pk=skill_id,
    )
    user_skill, created = UserSkill.objects.get_or_create(
        user=request.user,
        skill=skill,
        defaults={"started_on": timezone.localdate(), "is_active": True},
    )
    if not created:
        user_skill.is_active = not user_skill.is_active
        user_skill.save(update_fields=["is_active"])
    if user_skill.is_active:
        return redirect_to_preview(request, user_skill.id)
    return redirect_to_preview(
        request,
        posted_active_user_skill_id(request),
        return_to_library=request.POST.get("return_view") == "library",
    )


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
    if request.POST.get("return_view") == "dashboard":
        return redirect("dashboard-preview")
    return redirect(f"{reverse('dashboard-preview')}?skill={user_skill.id}")
