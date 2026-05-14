"""
0020 — Production-hardening migration for the orders app.

Adds:
  * Order.paid_at (nullable timestamp; populated by the webhook).
  * OrderItem.item_name_snapshot / item_photo_url_snapshot (preserve human-
    readable line items if the underlying product is later deleted).
  * db_index on Order.paid and Order.stripe_id; composite indexes for the
    common admin queries.

Loosens:
  * Order.user.on_delete: CASCADE -> SET_NULL  (keep order history when a
    user is deleted).
  * OrderItem.storeitem.on_delete: CASCADE -> SET_NULL + null=True
    (keep historical orders intact when a product is deleted).

This migration is purely additive at the data level — every existing row
remains valid.
"""

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0019_order_country_order_phone"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("TheApp", "0088_storeitems_order"),
    ]

    operations = [
        # ----- Order.user: CASCADE -> SET_NULL ---------------------------
        migrations.AlterField(
            model_name="order",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.deletion.SET_NULL,
                related_name="orders",
                to=settings.AUTH_USER_MODEL,
            ),
        ),

        # ----- Order.paid: add db_index ----------------------------------
        migrations.AlterField(
            model_name="order",
            name="paid",
            field=models.BooleanField(db_index=True, default=False),
        ),

        # ----- Order.stripe_id: add db_index -----------------------------
        migrations.AlterField(
            model_name="order",
            name="stripe_id",
            field=models.CharField(blank=True, db_index=True, max_length=250),
        ),

        # ----- Order.paid_at: new field ----------------------------------
        migrations.AddField(
            model_name="order",
            name="paid_at",
            field=models.DateTimeField(blank=True, null=True),
        ),

        # ----- OrderItem.storeitem: CASCADE -> SET_NULL (+nullable) ------
        migrations.AlterField(
            model_name="orderitem",
            name="storeitem",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.deletion.SET_NULL,
                related_name="order_items",
                to="TheApp.storeitems",
            ),
        ),

        # ----- OrderItem snapshot fields ---------------------------------
        migrations.AddField(
            model_name="orderitem",
            name="item_name_snapshot",
            field=models.CharField(blank=True, default="", max_length=200),
        ),
        migrations.AddField(
            model_name="orderitem",
            name="item_photo_url_snapshot",
            field=models.CharField(blank=True, default="", max_length=500),
        ),

        # ----- Composite indexes on Order --------------------------------
        # The new composite (paid, -created) index supersedes the old
        # ``-created`` index that was created in orders.0001_initial.
        migrations.RemoveIndex(
            model_name="order",
            name="orders_orde_created_743fca_idx",
        ),
        migrations.AddIndex(
            model_name="order",
            # Name matches Django's auto-generated naming so future
            # ``makemigrations`` runs detect no drift.
            index=models.Index(fields=["paid", "-created"], name="orders_orde_paid_98e2fa_idx"),
        ),
    ]
