"""
Order-related pricing helpers.

Builds Stripe Checkout ``line_items`` from an :class:`orders.models.Order`.
"""

from __future__ import annotations

from decimal import Decimal

from django.conf import settings

CENTS = Decimal("100")


def order_line_items_for_stripe(order) -> list[dict]:
    """Convert an Order's items into Stripe Checkout line_items.

    Uses the snapshotted ``item_name_snapshot`` if available so legacy
    orders whose original product has been deleted still describe correctly.
    """
    currency = getattr(settings, "STRIPE_CURRENCY", "usd").lower()
    line_items: list[dict] = []
    for item in order.items.all().select_related("storeitem"):
        unit_amount_cents = int(
            (Decimal(str(item.get_unit_price())) * CENTS).to_integral_value()
        )
        name = (
            item.item_name_snapshot
            or (item.storeitem.item_name if item.storeitem_id else f"Item #{item.id}")
        )
        line_items.append(
            {
                "price_data": {
                    "currency": currency,
                    "unit_amount": unit_amount_cents,
                    "product_data": {"name": name},
                },
                "quantity": item.quantity,
            }
        )
    return line_items
