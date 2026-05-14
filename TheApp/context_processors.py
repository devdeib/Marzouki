"""
Context processors for TheApp.

`sections(request)` provides a cached list of `Section` objects used by the
header / sidebar partials on virtually every page.  Pulling it from cache
avoids a DB query on every request.
"""

from __future__ import annotations

import logging

from django.core.cache import cache

logger = logging.getLogger(__name__)

_CACHE_KEY = "marzouki:sections:all:v1"
_CACHE_TTL = 60 * 5  # 5 minutes


def sections(request):  # noqa: D401 — Django context processor
    """Return ``{'global_sections': [Section, ...]}`` for templates.

    Templates already receive a per-view ``sections`` variable in many places;
    we expose ``global_sections`` here so partials can fall back to it without
    forcing every view to query the DB.
    """
    try:
        cached = cache.get(_CACHE_KEY)
        if cached is not None:
            return {"global_sections": cached}
    except Exception:  # pragma: no cover — Redis down etc.
        logger.warning("sections context_processor: cache.get failed", exc_info=True)
        cached = None

    try:
        # Local import keeps Django from importing models at settings-load time.
        from .models import Section

        result = list(Section.objects.all().order_by("name"))
    except Exception:  # pragma: no cover
        logger.exception("sections context_processor: DB query failed")
        return {"global_sections": []}

    try:
        cache.set(_CACHE_KEY, result, _CACHE_TTL)
    except Exception:  # pragma: no cover
        logger.warning("sections context_processor: cache.set failed", exc_info=True)

    return {"global_sections": result}


def invalidate_sections_cache() -> None:
    """Drop the cached Section list (called from signals on save/delete)."""
    try:
        cache.delete(_CACHE_KEY)
    except Exception:  # pragma: no cover
        logger.warning("invalidate_sections_cache: cache.delete failed", exc_info=True)
