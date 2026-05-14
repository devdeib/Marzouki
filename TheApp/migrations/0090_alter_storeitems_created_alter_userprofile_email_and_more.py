"""
0090 — Trailing model-state migrations and safe Discount CheckConstraint.

The AlterField operations are no-ops at the SQL level (Python-side
``auto_now_add`` change and CharField nullability that matches the
existing schema), but Django needs them recorded so future
``makemigrations`` runs stay clean.

The CheckConstraint ``discount_requires_section_or_item`` is added only
after a small data-cleanup ``RunPython`` step deletes any legacy
``Discount`` row that targets neither a section nor an item — without
that pre-step the constraint would fail on existing rows that the form
never validated.
"""

from django.db import migrations, models


def _clean_orphan_discounts(apps, schema_editor):
    """Delete Discount rows where both section_id and item_id are NULL.

    These rows can exist in legacy databases where the form-level guard
    wasn't always in place.  They're functionally inert (apply to
    nothing) so deletion is safe.
    """
    Discount = apps.get_model("TheApp", "Discount")
    Discount.objects.filter(section__isnull=True, item__isnull=True).delete()


def _noop(apps, schema_editor):
    """Reverse for the cleanup step (no-op; we can't resurrect dropped rows)."""
    return None


class Migration(migrations.Migration):

    dependencies = [
        ("TheApp", "0089_pricing_indexes_and_validators"),
    ]

    operations = [
        migrations.AlterField(
            model_name="storeitems",
            name="created",
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name="userprofile",
            name="email",
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name="userprofile",
            name="name",
            field=models.CharField(blank=True, max_length=200, null=True),
        ),

        # ---- Discount CheckConstraint (deferred until data is clean) ----
        migrations.RunPython(_clean_orphan_discounts, _noop),
        migrations.AddConstraint(
            model_name="discount",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ("section__isnull", False),
                    ("item__isnull", False),
                    _connector="OR",
                ),
                name="discount_requires_section_or_item",
            ),
        ),
    ]
