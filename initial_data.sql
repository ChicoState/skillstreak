-- SkillStreak initial shared data
--
-- Apply after schema.sql (or the equivalent Django migrations). This seed is
-- idempotent: it can be run again without creating duplicate system rows.
--
-- It intentionally contains no users, passwords, schedules, completions, or
-- measurements. Accounts belong to Django's authentication flow; schedules and
-- activity belong to the individual account that creates them.

BEGIN;

INSERT INTO skills (slug, name, description, visibility)
VALUES
    ('exercise', 'Exercise', 'Complete any exercise activity.', 'SYSTEM'),
    ('eat-healthy', 'Eat Healthy', 'Make a healthy eating choice.', 'SYSTEM'),
    ('read', 'Read', 'Spend time reading.', 'SYSTEM'),
    ('learn', 'Learn', 'Spend time learning something new.', 'SYSTEM'),
    ('touch-grass', 'Touch Grass', 'Spend time outdoors.', 'SYSTEM'),
    ('go-to-gym', 'Go to Gym', 'Visit the gym.', 'SYSTEM'),
    ('hobby', 'Hobby', 'Spend time on a hobby.', 'SYSTEM'),
    ('drink-water', 'Drink Water', 'Meet your hydration intention.', 'SYSTEM'),
    ('sleep', 'Sleep', 'Meet your sleep intention.', 'SYSTEM')
ON CONFLICT (slug) DO NOTHING;

INSERT INTO tags (slug, name)
VALUES
    ('active', 'Active'), ('outdoor', 'Outdoor'), ('wellness', 'Wellness'),
    ('nutrition', 'Nutrition'), ('sleep', 'Sleep'), ('mindfulness', 'Mindfulness'),
    ('social', 'Social'), ('home', 'Home'), ('productivity', 'Productivity'),
    ('learning', 'Learning'), ('creative', 'Creative'), ('finance', 'Finance'),
    ('career', 'Career'), ('digital', 'Digital'), ('environment', 'Environment'),
    ('pets', 'Pets'), ('community', 'Community'), ('self-care', 'Self-care'),
    ('general', 'General')
ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO tag_aliases (tag_id, term)
SELECT tags.id, aliases.term
FROM tags
JOIN (VALUES
    ('pets', 'cat'), ('pets', 'dog'), ('pets', 'puppy'), ('pets', 'kitten'), ('pets', 'animal'),
    ('outdoor', 'outside'), ('outdoor', 'nature'), ('social', 'friend'),
    ('active', 'exercise'), ('learning', 'study'), ('home', 'clean'), ('general', 'general')
) AS aliases(tag_slug, term) ON tags.slug = aliases.tag_slug
ON CONFLICT (tag_id, term) DO NOTHING;

INSERT INTO skill_tags (skill_id, tag_id)
SELECT skills.id, tags.id
FROM skills
JOIN (VALUES
    ('exercise', 'active'), ('exercise', 'wellness'),
    ('eat-healthy', 'nutrition'), ('read', 'learning'), ('learn', 'learning'),
    ('touch-grass', 'outdoor'), ('go-to-gym', 'active'), ('hobby', 'creative'),
    ('drink-water', 'nutrition'), ('sleep', 'sleep')
) AS assignments(skill_slug, tag_slug) ON skills.slug = assignments.skill_slug
JOIN tags ON tags.slug = assignments.tag_slug
ON CONFLICT (skill_id, tag_id) DO NOTHING;

COMMIT;
