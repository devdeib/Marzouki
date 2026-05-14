"""
Order and OrderItem models.
"""

from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models


class Order(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,  # keep order history if user is deleted
        null=True,
        blank=True,
        related_name="orders",
    )
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    phone = models.CharField(max_length=20, default="")
    country = models.CharField(max_length=100, default="")
    address = models.CharField(max_length=250)
    postal_code = models.CharField(max_length=20)
    city = models.CharField(max_length=100)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    paid = models.BooleanField(default=False, db_index=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    stripe_id = models.CharField(max_length=250, blank=True, db_index=True)

    class Meta:
        ordering = ["-created"]
        indexes = [
            # Composite covers both the listing ORDER BY (`-created`) and
            # the admin "unpaid" filter, so a standalone `-created` index
            # would be redundant.
            models.Index(fields=["paid", "-created"]),
        ]

    def __str__(self):
        return f"Order {self.id}"

    def get_total_cost(self) -> Decimal:
        return sum((item.get_cost() for item in self.items.all()), Decimal("0.00"))

    def get_stripe_url(self) -> str:
        if not self.stripe_id:
            return ""
        key = settings.STRIPE_SECRET_KEY or ""
        path = "/test/" if "_test_" in key else "/"
        return f"https://dashboard.stripe.com{path}payments/{self.stripe_id}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, related_name="items", on_delete=models.CASCADE
    )
    storeitem = models.ForeignKey(
        "TheApp.StoreItems",
        related_name="order_items",
        # Preserve order history if a product is deleted.
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    # Snapshot fields captured at order time so the line item stays
    # readable even if the underlying product is deleted later.
    item_name_snapshot = models.CharField(max_length=200, blank=True, default="")
    item_photo_url_snapshot = models.CharField(max_length=500, blank=True, default="")

    item_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    variations = models.JSONField(blank=True, null=True)
    choices = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"OrderItem {self.id} (order={self.order_id})"

    # ------------------------------------------------------------------
    # Pricing
    # ------------------------------------------------------------------
    @property
    def choice_increment(self) -> Decimal:
        total = Decimal("0.00")
        for c in (self.choices or []):
            try:
                total += Decimal(str(c.get("increment", 0)))
            except Exception:  # noqa: BLE001
                continue
        return total

    def get_unit_price(self) -> Decimal:
        """Per-unit price including all variation increments."""
        return (Decimal(str(self.item_price)) + self.choice_increment).quantize(
            Decimal("0.01")
        )

    def get_cost(self) -> Decimal:
        return (self.get_unit_price() * self.quantity).quantize(Decimal("0.01"))

    # ------------------------------------------------------------------
    # Template helpers (preserved from previous schema for template
    # backwards-compatibility).
    # ------------------------------------------------------------------
    @property
    def choices_list(self):
        return self.choices if isinstance(self.choices, list) else []

    @property
    def variations_list(self):
        return self.variations if isinstance(self.variations, list) else []
