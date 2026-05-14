"""
Catalog & profile models.
"""

from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import CheckConstraint, Q
from django.utils import timezone

from .validators import (
    image_extension_validator as _IMAGE_EXT_VALIDATOR,
    validate_image_size,
    validate_video_size,
    video_extension_validator as _VIDEO_EXT_VALIDATOR,
)


# ---------------------------------------------------------------------------
# User profile
# ---------------------------------------------------------------------------
class UserProfile(models.Model):
    user = models.OneToOneField(
        User, null=True, blank=True, on_delete=models.CASCADE
    )
    name = models.CharField(max_length=200, null=True, blank=True)
    email = models.CharField(max_length=200, null=True, blank=True)
    photo = models.ImageField(
        upload_to="profile_photos/",
        default="default.webp",
        null=True,
        blank=True,
        validators=[_IMAGE_EXT_VALIDATOR, validate_image_size],
    )

    def __str__(self):
        return self.user.username if self.user else f"Profile #{self.pk}"


# ---------------------------------------------------------------------------
# Taxonomy
# ---------------------------------------------------------------------------
class Size(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Variation(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Section(models.Model):
    CATEGORY_CHOICES = [
        ("OR", "Originals"),
        ("PR", "Prints"),
    ]

    name = models.CharField(max_length=200)
    category = models.CharField(
        max_length=2, choices=CATEGORY_CHOICES, default="OR"
    )
    items = models.ManyToManyField(
        "StoreItems", related_name="section", blank=True
    )

    def __str__(self):
        category_name = dict(self.CATEGORY_CHOICES).get(self.category, "Unknown")
        return f"{self.name} ({category_name})"


class Tag(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Color(models.Model):
    name = models.CharField(max_length=100)
    hex_value = models.CharField(max_length=7)

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# Store items
# ---------------------------------------------------------------------------
class StoreItems(models.Model):
    DRAFT = "DR"
    ACTIVE = "AC"
    INACTIVE = "IN"
    SHOWCASE = "SC"
    SOLD = "SO"

    STATUS_CHOICES = [
        (DRAFT, "Draft"),
        (ACTIVE, "Active"),
        (INACTIVE, "Inactive"),
        (SHOWCASE, "ShowCase"),
        (SOLD, "Sold"),
    ]

    status = models.CharField(
        max_length=2, choices=STATUS_CHOICES, default=DRAFT, db_index=True
    )
    item_name = models.CharField(max_length=200)
    item_price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))]
    )
    item_status = models.BooleanField(default=True)
    item_photo = models.ImageField(
        upload_to="items_media/",
        default="default.webp",
        null=True,
        blank=True,
        validators=[_IMAGE_EXT_VALIDATOR, validate_image_size],
    )
    item_description = models.TextField(blank=True)
    item_quantity = models.IntegerField(default=0)
    variations = models.ManyToManyField("Variation", through="ItemVariation")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    tags = models.ManyToManyField("Tag", blank=True)
    primary_color = models.ForeignKey(
        "Color",
        related_name="primary_color_items",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    secondary_color = models.ForeignKey(
        "Color",
        related_name="secondary_color_items",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    video = models.FileField(
        upload_to="items_videos/",
        null=True,
        blank=True,
        validators=[_VIDEO_EXT_VALIDATOR, validate_video_size],
    )
    width = models.FloatField(null=True, blank=True)
    height = models.FloatField(null=True, blank=True)
    order = models.PositiveIntegerField(default=0, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["status", "order"], name="storeitem_status_order_idx"),
        ]

    def __str__(self):
        return self.item_name

    def get_final_price(self) -> Decimal:
        """Return the effective price after the most relevant active discount.

        Centralized pricing logic lives in `cart.pricing`; this method
        delegates to it.
        """
        from cart.pricing import resolve_item_price

        return resolve_item_price(self)


class StoreItemImage(models.Model):
    item = models.ForeignKey(
        StoreItems, related_name="images", on_delete=models.CASCADE
    )
    image = models.ImageField(
        upload_to="items_media/",
        validators=[_IMAGE_EXT_VALIDATOR, validate_image_size],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.item.item_name} Image"


class StoreItemVideo(models.Model):
    item = models.ForeignKey(
        StoreItems, related_name="videos", on_delete=models.CASCADE
    )
    video_file = models.FileField(
        upload_to="items_videos/",
        validators=[_VIDEO_EXT_VALIDATOR, validate_video_size],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.item.item_name} Video"


# ---------------------------------------------------------------------------
# Variations
# ---------------------------------------------------------------------------
class ItemVariation(models.Model):
    item = models.ForeignKey(
        StoreItems, on_delete=models.CASCADE, related_name="item_variations"
    )
    variation = models.ForeignKey(Variation, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.item.item_name} - {self.variation.name}"

    class Meta:
        verbose_name_plural = "Item Variations"


class Choices(models.Model):
    variation = models.ForeignKey(
        "ItemVariation", related_name="choices", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=100)
    price_increment = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        default=None,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# Discounts
# ---------------------------------------------------------------------------
class Discount(models.Model):
    PERCENTAGE = "P"
    FIXED = "F"
    DISCOUNT_TYPE_CHOICES = [
        (PERCENTAGE, "Percentage"),
        (FIXED, "Fixed Amount"),
    ]

    section = models.ForeignKey(
        "Section", on_delete=models.SET_NULL, blank=True, null=True
    )
    item = models.ForeignKey(
        "StoreItems", on_delete=models.SET_NULL, blank=True, null=True
    )
    discount_type = models.CharField(
        max_length=1, choices=DISCOUNT_TYPE_CHOICES
    )
    discount_value = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))]
    )
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    class Meta:
        indexes = [
            models.Index(fields=["start_date", "end_date"], name="discount_window_idx"),
        ]
        constraints = [
            CheckConstraint(
                check=(Q(section__isnull=False) | Q(item__isnull=False)),
                name="discount_requires_section_or_item",
            ),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.section is None and self.item is None:
            raise ValidationError("A discount must target either a section or an item.")
        if self.section is not None and self.item is not None:
            raise ValidationError("A discount cannot target both a section and an item.")
        if self.end_date <= self.start_date:
            raise ValidationError("Discount end date must be after the start date.")

    def calculate_new_price(self, original_price) -> Decimal:
        original = Decimal(str(original_price))
        now = timezone.now()
        if not (self.start_date <= now <= self.end_date):
            return original
        value = Decimal(str(self.discount_value))
        if self.discount_type == self.PERCENTAGE:
            return (original * (Decimal("100") - value) / Decimal("100")).quantize(Decimal("0.01"))
        if self.discount_type == self.FIXED:
            return max(original - value, Decimal("0.00")).quantize(Decimal("0.01"))
        return original

    def __str__(self):
        scope = "Section" if self.section else "Item"
        return f"{scope} Discount: {self.discount_value} ({self.get_discount_type_display()})"


# ---------------------------------------------------------------------------
# Newsletter
# ---------------------------------------------------------------------------
class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = "Newsletter Subscriber"
        verbose_name_plural = "Newsletter Subscribers"

    def __str__(self):
        return self.email


# ---------------------------------------------------------------------------
# Artist profile (singleton)
# ---------------------------------------------------------------------------
class ArtistProfile(models.Model):
    bio = models.TextField(blank=True)
    photo = models.ImageField(
        upload_to="artist_photos/",
        blank=True,
        null=True,
        validators=[_IMAGE_EXT_VALIDATOR, validate_image_size],
    )
    updated_at = models.DateTimeField(auto_now=True)
    twitter_url = models.URLField(blank=True, default="")
    twitter_show = models.BooleanField(default=False)
    instagram_url = models.URLField(blank=True, default="")
    instagram_show = models.BooleanField(default=False)
    facebook_url = models.URLField(blank=True, default="")
    facebook_show = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Artist Profile"
        verbose_name_plural = "Artist Profile"

    def __str__(self):
        return "Artist Profile"

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


# ---------------------------------------------------------------------------
# Legacy session-cart DB model (retained for backwards compatibility with
# existing migrations; the live cart is session-based in `cart.cart.Cart`).
# ---------------------------------------------------------------------------
class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(
        StoreItems,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        default=None,
    )

    def __str__(self):
        return f"{self.user.username} - {self.item}"
