"""Prevent overlapping schedule periods for the same selected skill."""

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("tracking", "0002_metricdefinition_metric_definitions_nonempty_key_and_more")]

    operations = [
        migrations.RunSQL(
            sql="CREATE EXTENSION IF NOT EXISTS btree_gist;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql=(
                "ALTER TABLE user_skill_schedules "
                "ADD CONSTRAINT user_skill_schedules_no_date_overlap "
                "EXCLUDE USING gist ("
                "user_skill_id WITH =, "
                "daterange(effective_from, "
                "COALESCE(effective_through + 1, 'infinity'::date), '[)') WITH &&"
                ");"
            ),
            reverse_sql=(
                "ALTER TABLE user_skill_schedules "
                "DROP CONSTRAINT user_skill_schedules_no_date_overlap;"
            ),
        ),
    ]
