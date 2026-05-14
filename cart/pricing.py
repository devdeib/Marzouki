"""
Centralized pricing logic for the catalog and cart.

This is the **single source of truth** for "what price does the customer pay
for product X right now?".  Used by:

* ``TheApp.models.StoreItems.get_final_price``
* ``cart.cart.Cart`` (per-line and total computation)
* ``orders.views.order_create`` / ``checkout_summary`` (Stripe line items)

All arithmetic is performed in :class:`decimal.Decimal` to avoid float
rounding errors that would otherwise propagate into Stripe ``unit_amount``.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Iterable

from django.utils import timezone

CENTS = Decimal("0.01")
ZERO = Decimal("0.00")


def to_decimal(value) -> Decimal:
    """Best-effort conversion to a 2-decimal-place :class:`Decimal`."""
    if value is None:
        return ZERO
    try:
        return Decimal(str(value)).quantize(CENTS)
    except (InvalidOperation, ValueError, TypeError):
        return ZERO


def _best_discount_for_item(item):
    """Return the most relevant active :class:`Discount` for ``item``, or ``None``.

    Priority:
      1. An item-specific active discount.
      2. A section-wide active discount covering one of the item's sections.
    """
    # Local imports avoid app-loading-order issues.
    from TheApp.models import Discount

    now = timezone.now()

    item_discount = (
        item.discount_set.filter(start_date__lte=now, end_date__gte=now).first()
        if hasattr(item, "discount_set")
        else None
    )
    if item_discount:
        return item_discount

    return (
        Discount.objects.filter(
            section__in=item.section.all(),
            start_date__lte=now,
            end_date__gte=now,
        ).first()
    )


def resolve_item_price(item) -> Decimal:
    """Effective customer-facing unit price for a :class:`StoreItems` instance.

    Honors the most relevant active discount.  Never raises — falls back to
    the raw ``item_price`` on any error so the catalog page still renders.
    """
    base = to_decimal(item.item_price)
    try:
        discount = _best_discount_for_item(item)
    except Exception:  # noqa: BLE001 — never break catalog pages
        return base

    if discount is None:
        return base

    try:
        return to_decimal(discount.calculate_new_price(base))
    except Exception:  # noqa: BLE001
        return base


def discount_percent(base_price, final_price) -> int:
    """Return the integer percentage off (0–100), or 0 if base is non-positive."""
    base = to_decimal(base_price)
    final = to_decimal(final_price)
    if base <= ZERO or final >= base:
        return 0
    return int(((base - final) / base) * Decimal("100"))


def variation_increment(variation_choices: Iterable[dict] | None) -> Decimal:
    """Sum the ``price_increment`` values across a list of selected variation
    choices (the dict shape stored in the session cart)."""
    total = ZERO
    if not variation_choices:
        return total
    for choice in variation_choices:
        if not isinstance(choice, dict):
            continue
        total += to_decimal(choice.get("price_increment", 0))
    return total


def line_total(item, variation_choices, quantity: int) -> dict[str, Decimal]:
    """Compute base / final / total prices for a single cart line.

    Returns a dict with Decimal values:
      - ``base_price``  : unit price ignoring discounts
      - ``unit_price``  : discounted unit price
      - ``increment``   : variation-choice add-on
      - ``final_price`` : ``unit_price + increment``
      - ``total_price`` : ``final_price * quantity``
    """
    base_price = to_decimal(item.item_price)
    unit_price = resolve_item_price(item)
    increment = variation_increment(variation_choices)
    final_price = (unit_price + increment).quantize(CENTS)
    qty = max(int(quantity or 0), 0)
    total_price = (final_price * qty).quantize(CENTS)
    return {
        "base_price": base_price,
        "unit_price": unit_price,
        "increment": increment,
        "final_price": final_price,
        "total_price": total_price,
    }
