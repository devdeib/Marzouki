"""
Session-based shopping cart.

The cart is stored as a JSON-safe dict inside ``request.session``.  All money
values are stored as strings (decimal text) so they survive JSON
serialization without precision loss, then converted to :class:`Decimal`
when needed for arithmetic.
"""

from __future__ import annotations

import logging
from decimal import Decimal

from django.conf import settings

from .pricing import (
    CENTS,
    ZERO,
    line_total,
    resolve_item_price,
    to_decimal,
    variation_increment,
)

logger = logging.getLogger(__name__)


class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------
    def save(self) -> None:
        self.session.modified = True

    def add(
        self,
        item,
        quantity: int = 1,
        variation_choice_list=None,
        personalization: str | None = None,
        override_quantity: bool = False,
        variation_key=None,
        variation_keys=None,
    ) -> None:
        """Add a product (with optional variation choices) to the cart."""
        variation_choice_list = variation_choice_list or []

        # Normalize stored price_increment to plain floats (JSON-safe).
        for choice in variation_choice_list:
            try:
                choice["price_increment"] = float(choice.get("price_increment", 0) or 0)
            except (TypeError, ValueError):
                choice["price_increment"] = 0.0

        # Unique cart-line key combines the product id with the variation
        # selections so the same product with different choices = different lines.
        variation_str = "-".join(
            f"{c.get('variation_name', '')}:{c.get('choice_name', '')}"
            for c in variation_choice_list
        )
        cart_item_id = f"{item.id}--{variation_str}" if variation_str else str(item.id)

        if cart_item_id not in self.cart:
            self.cart[cart_item_id] = {
                "item_id": item.id,
                "quantity": 0,
                # Stored as strings to survive JSON serialization without
                # rounding errors.
                "item_price": str(to_decimal(item.item_price)),
                "item_name": item.item_name,
                "item_description": item.item_description or "",
                "item_photo": item.item_photo.url if item.item_photo else "",
                "personalization": personalization or "",
                "variation_choices": variation_choice_list,
                "variation_key": variation_keys if variation_keys else None,
            }

        try:
            quantity = max(int(quantity or 0), 0)
        except (TypeError, ValueError):
            quantity = 0

        if override_quantity:
            self.cart[cart_item_id]["quantity"] = quantity
        else:
            self.cart[cart_item_id]["quantity"] += quantity

        # Drop zero/negative lines and cap extreme quantities.
        if cart_item_id in self.cart:
            qty = self.cart[cart_item_id]["quantity"]
            if qty <= 0:
                del self.cart[cart_item_id]
            elif qty > 9999:
                self.cart[cart_item_id]["quantity"] = 9999

        self.save()

    def remove(self, item_id) -> None:
        """Remove every line matching the given product id (strips variations)."""
        item_id_str = str(item_id)
        removed = False
        for key in list(self.cart.keys()):
            # Match either exact product id or the variation-prefixed form
            # ``<id>--<variation>``.
            if key == item_id_str or key.startswith(f"{item_id_str}--"):
                del self.cart[key]
                removed = True
        if removed:
            self.save()

    def clear(self) -> None:
        self.session[settings.CART_SESSION_ID] = {}
        self.save()

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------
    def __len__(self) -> int:
        return sum(int(item.get("quantity", 0) or 0) for item in self.cart.values())

    def _fetch_products(self) -> dict:
        """Bulk-fetch all products in the cart in a single query."""
        from TheApp.models import StoreItems

        ids = [int(data["item_id"]) for data in self.cart.values() if data.get("item_id")]
        if not ids:
            return {}
        return {p.id: p for p in StoreItems.objects.filter(id__in=ids)}

    def __iter__(self):
        products_by_id = self._fetch_products()
        cart_items_to_remove: list[str] = []

        for cart_item_id, data in self.cart.items():
            item = products_by_id.get(data.get("item_id"))
            if item is None:
                cart_items_to_remove.append(cart_item_id)
                continue

            quantity = int(data.get("quantity", 0) or 0)
            if quantity <= 0:
                cart_items_to_remove.append(cart_item_id)
                continue

            variation_choices = data.get("variation_choices", []) or []

            try:
                totals = line_total(item, variation_choices, quantity)
            except Exception:  # noqa: BLE001
                logger.exception("Cart line pricing failed for cart_item_id=%s", cart_item_id)
                continue

            yield {
                "item_id": item.id,
                "item_name": item.item_name,
                "item_photo": item.item_photo.url if item.item_photo else "",
                "quantity": quantity,
                "item_price": float(totals["base_price"]),
                "final_price": float(totals["final_price"]),
                "discount_percent": 0,  # populated by views that want it
                "total_price": float(totals["total_price"]),
                "variation_choices": variation_choices,
                "personalization": data.get("personalization", ""),
            }

        if cart_items_to_remove:
            for key in cart_items_to_remove:
                self.cart.pop(key, None)
            self.save()

    def get_total_price(self) -> Decimal:
        """Return the cart total as a :class:`Decimal`."""
        products_by_id = self._fetch_products()
        total = ZERO
        for data in self.cart.values():
            item = products_by_id.get(data.get("item_id"))
            if item is None:
                continue
            try:
                quantity = int(data.get("quantity", 0) or 0)
            except (TypeError, ValueError):
                quantity = 0
            base = resolve_item_price(item)
            inc = variation_increment(data.get("variation_choices", []))
            total += (base + inc) * quantity
        return total.quantize(CENTS)
