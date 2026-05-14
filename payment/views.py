"""
Payment views.

The Stripe Checkout success URL (``payment_completed``) is a **passive
thank-you page**: it never trusts the user's session for payment state.
The single source of truth is :mod:`payment.webhooks` which is signed by
Stripe.

For projects that have not configured a webhook yet, ``payment_completed``
falls back to the legacy behavior (marks the order paid based on the
session's ``order_id``) so that the live store keeps working during the
deployment cutover.  Set ``STRIPE_WEBHOOK_SECRET`` to disable the fallback.
"""

from __future__ import annotations

import logging

import stripe
from django.conf import settings
from django.shortcuts import get_object_or_404, render

from cart.cart import Cart
from orders.models import Order

stripe.api_key = settings.STRIPE_SECRET_KEY

logger = logging.getLogger("payment")


def payment_process(request):
    """Re-create a Stripe Checkout Session from the in-session order.

    NOTE: the primary checkout flow now goes through
    ``orders.views.checkout_summary`` which builds the same session.  This
    view is kept for backward-compatibility with the ``payment:process``
    URL referenced in older templates (process.html).
    """
    from orders.services.pricing import order_line_items_for_stripe  # local import

    order_id = request.session.get("order_id")
    order = get_object_or_404(Order, id=order_id)

    session = stripe.checkout.Session.create(
        mode="payment",
        client_reference_id=order.id,
        success_url=request.build_absolute_uri("/payment/completed/"),
        cancel_url=request.build_absolute_uri("/payment/canceled/"),
        line_items=order_line_items_for_stripe(order),
    )
    return _redirect_to_url(session.url)


def _redirect_to_url(url: str):
    """Helper: 303 redirect (Stripe recommended for Checkout)."""
    from django.shortcuts import redirect

    return redirect(url, code=303)


def payment_completed(request):
    """Show the success page.  Do **not** mutate ``Order.paid`` here unless
    the webhook is unconfigured (legacy fallback)."""
    order_id = request.session.get("order_id")
    order = None
    if order_id:
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            order = None

    # Clean up the session so refreshing the page doesn't pin a stale id.
    if order_id:
        try:
            cart = Cart(request)
            cart.clear()
            request.session.pop("order_id", None)
            request.session.save()
        except Exception:  # pragma: no cover
            logger.exception("payment_completed: session cleanup failed")

    # ------------------------------------------------------------------
    # Legacy fallback (transitional, will be removed once webhook is live):
    # if STRIPE_WEBHOOK_SECRET is *unset*, retain the original behavior of
    # marking the order paid from the success URL.  Logged loudly.
    # ------------------------------------------------------------------
    webhook_secret = getattr(settings, "STRIPE_WEBHOOK_SECRET", "") or ""
    if order is not None and not webhook_secret and not order.paid:
        logger.warning(
            "payment_completed: STRIPE_WEBHOOK_SECRET is empty — marking "
            "order #%s paid via the legacy success-URL path. Configure the "
            "webhook ASAP.",
            order.id,
        )
        Order.objects.filter(id=order.id).update(paid=True)
        order.paid = True

    return render(request, "completed.html", {"order_id": order_id, "order": order})


def payment_canceled(request):
    return render(request, "canceled.html")
