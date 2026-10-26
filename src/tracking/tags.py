"""Curated tag taxonomy and deterministic local matching rules."""

import re

TAG_DEFINITIONS = (
    ("active", "Active", ("exercise", "gym", "walk", "run", "cycle", "dance", "yoga", "hike")),
    ("outdoor", "Outdoor", ("outside", "outdoor", "nature", "sun", "grass", "hike")),
    ("wellness", "Wellness", ("health", "posture", "breathing", "stretch", "balance")),
    (
        "nutrition",
        "Nutrition",
        ("meal", "food", "fruit", "vegetable", "water", "hydration", "recipe"),
    ),
    ("sleep", "Sleep", ("sleep", "bed", "bedtime", "caffeine")),
    ("mindfulness", "Mindfulness", ("meditate", "gratitude", "patience", "calming")),
    ("social", "Social", ("friend", "family", "someone", "compliment", "thank", "listening")),
    ("home", "Home", ("laundry", "dishes", "kitchen", "bathroom", "clean", "tidy", "declutter")),
    ("productivity", "Productivity", ("plan", "priority", "focus", "task", "calendar", "inbox")),
    ("learning", "Learning", ("learn", "study", "practice", "tutorial", "notes", "fact", "math")),
    ("creative", "Creative", ("draw", "write", "photo", "creative", "instrument", "fiction")),
    ("finance", "Finance", ("budget", "spending", "money", "bill", "savings")),
    ("career", "Career", ("resume", "presentation", "network", "coding")),
    ("digital", "Digital", ("screen", "files", "photos", "typing", "podcast")),
    ("environment", "Environment", ("recycle", "energy", "reusable", "plants")),
    ("pets", "Pets", ("pet", "pets", "cat", "cats", "dog", "dogs", "puppy", "kitten", "animal")),
    ("community", "Community", ("volunteer", "community", "helping")),
    ("self-care", "Self-care", ("shower", "skincare", "clothes", "break", "appointment")),
    ("general", "General", ()),
)


def tag_slugs_for_text(name: str, description: str, limit: int = 3) -> tuple[str, ...]:
    """Choose the highest-scoring curated tags, with a deterministic fallback."""
    text = f"{name} {description}".lower()
    scored_tags: list[tuple[int, int, str]] = []
    for order, (slug, tag_name, aliases) in enumerate(TAG_DEFINITIONS):
        if slug == "general":
            continue
        terms = (tag_name.lower(), *aliases)
        score = sum(len(re.findall(rf"\b{re.escape(term)}\b", text)) for term in terms)
        if score:
            scored_tags.append((-score, order, slug))
    if not scored_tags:
        return ("general",)
    return tuple(slug for _, _, slug in sorted(scored_tags)[:limit])
