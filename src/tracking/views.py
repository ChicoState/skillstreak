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
from .library import available_library_skills, normalize_library_query
from .models import DailyCompletion, Skill, SkillTag, Tag, UserSkill, UserSkillSchedule
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
            matching_slugs = tag_slugs_for_text(skill.name, skill.description, limit=99)
            tags_by_slug = Tag.objects.in_bulk(matching_slugs, field_name="slug")
            matching_tag = next(
                (tags_by_slug[slug] for slug in matching_slugs if slug in tags_by_slug), None
            )
            if matching_tag is not None:
                SkillTag.objects.create(skill=skill, tag=matching_tag)
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
    completion, created = DailyCompletion.objects.get_or_create(
        user_skill=user_skill, completed_on=timezone.localdate()
    )
    if not created:
        completion.delete()
    if request.POST.get("return_view") == "dashboard":
        return redirect("dashboard-preview")
    return redirect(f"{reverse('dashboard-preview')}?skill={user_skill.id}")
