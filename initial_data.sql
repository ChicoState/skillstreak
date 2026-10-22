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

COMMIT;
