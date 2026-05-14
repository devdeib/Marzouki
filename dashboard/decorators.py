"""
Dashboard auth decorators.

Centralizes the "must be authenticated staff" gate so every view in the
dashboard is protected even if someone forgets to add the decorator
on a new view.
"""

from __future__ import annotations

from functools import wraps

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required


def staff_required(view_func):
    """Decorator: must be authenticated AND ``is_staff=True``.

    Equivalent to ``@staff_member_required(login_url=settings.LOGIN_URL)``
    but easier to compose with other decorators.
    """

    @wraps(view_func)
    @login_required
    @staff_member_required
    def _wrapped(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)

    return _wrapped
