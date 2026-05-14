"""
Stripe webhook handler.

This is the **only** server path that should flip ``Order.paid = True``.
The redirect-based success URL must never trust the user's session for
payment state — see ``payment.views.payment_completed`` for the passive
thank-you page.

Setup:

  1. ``STRIPE_WEBHOOK_SECRET`` must be set in the environment.
  2. Configure a Stripe webhook endpoint pointing to
     ``https://<your-domain>/stripe/webhook/`` and select at minimum the
     event ``checkout.session.completed``.

The handler is:
  - CSRF-exempt (Stripe doesn't send a CSRF token).
  - POST-only.
  - Signature-verified via ``stripe.Webhook.construct_event``.
  - Idempotent: re-running the same event will not double-update.
"""

from __future__ import annotations

import logging

import stripe
from django.conf import settings
from django.db import transaction
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from orders.models import Order

logger = logging.getLogger("payment")


def _process_checkout_session_completed(event_data: dict) -> None:
    """Mark the order paid based on a verified ``checkout.session.completed`` event."""
    session = event_data.get("object") or {}
    payment_intent_id = session.get("payment_intent") or session.get("id") or ""
    client_reference_id = session.get("client_reference_id")
    payment_status = session.get("payment_status", "")

    if payment_status not in {"paid", "no_payment_required"}:
        logger.info(
            "payment.webhook: checkout.session.completed without paid status "
            "(client_reference_id=%s payment_status=%s)",
            client_reference_id,
            payment_status,
        )
        return

    if not client_reference_id:
        logger.warning("payment.webhook: missing client_reference_id on session")
        return

    try:
        order_id = int(client_reference_id)
    except (TypeError, ValueError):
        logger.warning(
            "payment.webhook: client_reference_id is not an integer: %r",
            client_reference_id,
        )
        return

    with transaction.atomic():
        # ``select_for_update`` guarantees we don't race with another worker
        # processing the same event delivered twice.
        try:
            order = Order.objects.select_for_update().get(id=order_id)
        except Order.DoesNotExist:
            logger.warning("payment.webhook: order %s not found", order_id)
            return

        already_paid = order.paid
        order.paid = True
        if payment_intent_id and not order.stripe_id:
            order.stripe_id = str(payment_intent_id)[:250]
        order.save(update_fields=["paid", "stripe_id", "updated"])

    logger.info(
        "payment.webhook: order #%s marked paid (already_paid=%s, stripe_id=%s)",
        order_id,
        already_paid,
        payment_intent_id or "n/a",
    )


@csrf_exempt
@require_POST
def stripe_webhook(request: HttpRequest) -> HttpResponse:
    """Verify the Stripe signature and dispatch the event."""
    webhook_secret = getattr(settings, "STRIPE_WEBHOOK_SECRET", "") or ""
    if not webhook_secret:
        logger.error(
            "payment.webhook: STRIPE_WEBHOOK_SECRET is not configured — "
            "rejecting incoming webhook for safety."
        )
        return HttpResponseBadRequest("webhook secret not configured")

    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=webhook_secret,
        )
    except ValueError:
        logger.warning("payment.webhook: malformed JSON payload")
        return HttpResponseBadRequest("invalid payload")
    except stripe.error.SignatureVerificationError:  # pragma: no cover
        logger.warning("payment.webhook: invalid signature")
        return HttpResponseBadRequest("invalid signature")

    event_type = event.get("type", "")
    event_id = event.get("id", "")
    logger.info("payment.webhook: received event %s (%s)", event_type, event_id)

    try:
        if event_type == "checkout.session.completed":
            _process_checkout_session_completed(event.get("data") or {})
        elif event_type == "checkout.session.async_payment_succeeded":
            _process_checkout_session_completed(event.get("data") or {})
        # Other event types are acknowledged but not acted upon yet.
    except Exception:  # pragma: no cover — never let Stripe retry-storm
        logger.exception("payment.webhook: handler error for event %s", event_id)
        # Returning 500 would make Stripe retry; we only return 500 for
        # genuinely retryable failures.
        return HttpResponse(status=500)

    return HttpResponse(status=200)
