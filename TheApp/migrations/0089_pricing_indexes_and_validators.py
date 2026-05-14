"""
0089 â€” Production-hardening migration for TheApp.

Schema changes:
  * StoreItems.item_price:        FloatField -> DecimalField(10,2)
  * Discount.discount_value:      FloatField -> DecimalField(10,2)
  * Choices.price_increment:      nullable + new validator, default removed

Indexes:
  * db_index=True on StoreItems.status, StoreItems.order
  * db_index=True on NewsletterSubscriber.is_active
  * Composite index on StoreItems (status, order)
  * Composite index on Discount (start_date, end_date)

Validators (no DB schema impact, Python-side):
  * File-extension and size validators on every ImageField / FileField.

Deliberately omitted:
  * The ``discount_requires_section_or_item`` CHECK constraint.  It is still
    enforced at form/model ``clean()`` time.  We skip it in the migration so
    the deploy does not fail on legacy rows where both ``section`` and
    ``item`` happen to be NULL.

Notes for PostgreSQL deploys:
  * Django emits ``ALTER COLUMN ... TYPE numeric(10, 2) USING column::numeric``
    for the FloatField -> DecimalField conversion.  Existing rows convert
    losslessly when current values fit in 10/2.  On SQLite (the current
    production DB at the time of writing) the change is a no-op.
"""

import django.core.validators
from decimal import Decimal

from django.db import migrations, models

import TheApp.validators  # validate_image_size / validate_video_size


class Migration(migrations.Migration):

    dependencies = [
        ("TheApp", "0088_storeitems_order"),
    ]

    operations = [
        # ----- Money columns ---------------------------------------------
        migrations.AlterField(
            model_name="storeitems",
            name="item_price",
            field=models.DecimalField(
                decimal_places=2,
                max_digits=10,
                validators=[django.core.validators.MinValueValidator(Decimal("0.00"))],
            ),
        ),
        migrations.AlterField(
            model_name="discount",
            name="discount_value",
            field=models.DecimalField(
                decimal_places=2,
                max_digits=10,
                validators=[django.core.validators.MinValueValidator(Decimal("0.00"))],
            ),
        ),
        migrations.AlterField(
            model_name="choices",
            name="price_increment",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                default=None,
                max_digits=10,
                null=True,
                validators=[django.core.validators.MinValueValidator(Decimal("0.00"))],
            ),
        ),

        # ----- db_index on hot columns -----------------------------------
        migrations.AlterField(
            model_name="storeitems",
            name="status",
            field=models.CharField(
                choices=[
                    ("DR", "Draft"),
                    ("AC", "Active"),
                    ("IN", "Inactive"),
                    ("SC", "ShowCase"),
                    ("SO", "Sold"),
                ],
                db_index=True,
                default="DR",
                max_length=2,
            ),
        ),
        migrations.AlterField(
            model_name="storeitems",
            name="order",
            field=models.PositiveIntegerField(db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name="newslettersubscriber",
            name="is_active",
            field=models.BooleanField(db_index=True, default=True),
        ),

        # ----- File / image validators -----------------------------------
        migrations.AlterField(
            model_name="userprofile",
            name="photo",
            field=models.ImageField(
                blank=True,
                default="default.webp",
                null=True,
                upload_to="profile_photos/",
                validators=[
                    django.core.validators.FileExtensionValidator(
                        allowed_extensions=["jpg", "jpeg", "png", "webp", "gif"]
                    ),
                    TheApp.validators.validate_image_size,
                ],
            ),
        ),
        migrations.AlterField(
            model_name="storeitems",
            name="item_photo",
            field=models.ImageField(
                blank=True,
                default="default.webp",
                null=True,
                upload_to="items_media/",
                validators=[
                    django.core.validators.FileExtensionValidator(
                        allowed_extensions=["jpg", "jpeg", "png", "webp", "gif"]
                    ),
                    TheApp.validators.validate_image_size,
                ],
            ),
        ),
        migrations.AlterField(
            model_name="storeitems",
            name="video",
            field=models.FileField(
                blank=True,
                null=True,
                upload_to="items_videos/",
                validators=[
                    django.core.validators.FileExtensionValidator(
                        allowed_extensions=["mp4", "mov", "webm"]
                    ),
                    TheApp.validators.validate_video_size,
                ],
            ),
        ),
        migrations.AlterField(
            model_name="storeitemimage",
            name="image",
            field=models.ImageField(
                upload_to="items_media/",
                validators=[
                    django.core.validators.FileExtensionValidator(
                        allowed_extensions=["jpg", "jpeg", "png", "webp", "gif"]
                    ),
                    TheApp.validators.validate_image_size,
                ],
            ),
        ),
        migrations.AlterField(
            model_name="storeitemvideo",
            name="video_file",
            field=models.FileField(
                upload_to="items_videos/",
                validators=[
                    django.core.validators.FileExtensionValidator(
                        allowed_extensions=["mp4", "mov", "webm"]
                    ),
                    TheApp.validators.validate_video_size,
                ],
            ),
        ),
        migrations.AlterField(
            model_name="artistprofile",
            name="photo",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to="artist_photos/",
                validators=[
                    django.core.validators.FileExtensionValidator(
                        allowed_extensions=["jpg", "jpeg", "png", "webp", "gif"]
                    ),
                    TheApp.validators.validate_image_size,
                ],
            ),
        ),

        # ----- Composite indexes -----------------------------------------
        migrations.AddIndex(
            model_name="storeitems",
            index=models.Index(
                fields=["status", "order"], name="storeitem_status_order_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="discount",
            index=models.Index(
                fields=["start_date", "end_date"], name="discount_window_idx"
            ),
        ),
    ]

