"""
Signal handlers for TheApp.

Currently used only to invalidate the cached `Section` list whenever a
section is created, edited, or deleted.
"""

from __future__ import annotations

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from TheApp.context_processors import invalidate_sections_cache
from TheApp.models import Section


@receiver(post_save, sender=Section)
@receiver(post_delete, sender=Section)
def _bust_sections_cache(sender, **kwargs):  # noqa: D401
    invalidate_sections_cache()
