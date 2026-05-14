"""Additional security headers for HTML responses (CSP, Permissions-Policy)."""

from __future__ import annotations

from django.conf import settings

_HTML_CTYPES = frozenset({"text/html", "application/xhtml+xml"})


def _content_security_policy() -> str:
    custom = getattr(settings, "CONTENT_SECURITY_POLICY", None)
    if isinstance(custom, str) and custom.strip():
        return custom.strip()
    # Mirrors current CDNs and Stripe; allows inline scripts/styles used across templates.
    parts = [
        "default-src 'self'",
        (
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net "
            "https://cdnjs.cloudflare.com https://stackpath.bootstrapcdn.com https://js.stripe.com"
        ),
        (
            "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com "
            "https://stackpath.bootstrapcdn.com https://fonts.googleapis.com"
        ),
        "img-src 'self' data: https: blob:",
        (
            "font-src 'self' https://cdnjs.cloudflare.com "
            "https://fonts.gstatic.com data:"
        ),
        (
            "connect-src 'self' https://api.stripe.com https://r.stripe.com "
            "https://m.stripe.network"
        ),
        "frame-src https://js.stripe.com https://hooks.stripe.com https://m.stripe.network",
        "media-src 'self' blob: data:",
        "base-uri 'self'",
        "form-action 'self'",
        "frame-ancestors 'none'",
    ]
    if not settings.DEBUG:
        parts.append("upgrade-insecure-requests")
    return "; ".join(parts) + ";"


class ContentSecurityPolicyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        ctype = response.get("Content-Type", "").split(";")[0].strip().lower()
        if ctype not in _HTML_CTYPES:
            return response
        if response.get("Content-Security-Policy"):
            return response
        response["Content-Security-Policy"] = _content_security_policy()
        response.setdefault(
            "Permissions-Policy",
            (
                "accelerometer=(), camera=(), geolocation=(), gyroscope=(), "
                "magnetometer=(), microphone=(), payment=(), usb=()"
            ),
        )
        return response
