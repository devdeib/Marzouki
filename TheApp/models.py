from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
# Create your models here


class UserProfile(models.Model):

    user = models.OneToOneField(
        User, null=True, blank=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, null=True)
    email = models.CharField(max_length=200, null=True)
    photo = models.ImageField(
        upload_to='media/profile_photos/', default="default.webp", null=True, blank=True)


class Size(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Variation(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Section(models.Model):
    name = models.CharField(max_length=200)
    items = models.ManyToManyField(
        'StoreItems', related_name='section', blank=True)

    def str(self):
        return self.name


class StoreItems(models.Model):
    DRAFT = 'DR'
    ACTIVE = 'AC'
    INACTIVE = 'IN'
    STATUS_CHOICES = [
        (DRAFT, 'Draft'),
        (ACTIVE, 'Active'),
        (INACTIVE, 'Inactive'),
    ]

    status = models.CharField(
        max_length=2, choices=STATUS_CHOICES, default=DRAFT)
    item_name = models.CharField(max_length=200)
    item_price = models.FloatField(null=False)
    item_status = models.BooleanField(default=True)
    item_photo = models.ImageField(
        upload_to='items_media/', default="default.webp", null=True, blank=True)
    item_description = models.TextField(blank=True)
    item_quantity = models.IntegerField(default=0)  # Add the quantity field
    variations = models.ManyToManyField('Variation', through='ItemVariation')
    item_variations = models.ManyToManyField(
        'ItemVariation', blank=True, default=True)  # Add this line

    created = models.DateTimeField(auto_now=True)
    updated = models.DateTimeField(auto_now=True)
    tags = models.ManyToManyField('Tag', blank=True)
    primary_color = models.ForeignKey(
        'Color', related_name='primary_color_items', blank=True, null=True, on_delete=models.SET_NULL)
    secondary_color = models.ForeignKey(
        'Color', related_name='secondary_color_items', blank=True, null=True, on_delete=models.SET_NULL)
    video = models.FileField(upload_to='items_videos/', null=True, blank=True)
    width = models.FloatField(
        null=True, blank=True)
    height = models.FloatField(
        null=True, blank=True)


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(
        StoreItems, on_delete=models.CASCADE, blank=True, null=True, default=None)

    def __str__(self):
        return f"{self.user.username} - {self.item}"


class Tag(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Color(models.Model):
    name = models.CharField(max_length=100)
    hex_value = models.CharField(max_length=7)

    def __str__(self):
        return self.name


class Choices(models.Model):
    variation = models.ForeignKey(
        'ItemVariation', related_name='choices', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    price_increment = models.FloatField(
        blank=True, null=True, default=None)

    def __str__(self):
        return self.name


class ItemVariation(models.Model):
    item = models.ForeignKey(StoreItems, on_delete=models.CASCADE)
    variation = models.ForeignKey(Variation, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.item.item_name} - {self.variation.name}"


class StoreItemImage(models.Model):
    item = models.ForeignKey(StoreItems, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='items_media/')

    def __str__(self):
        return f"{self.item.item_name} Image"


class Discount(models.Model):
    PERCENTAGE = 'P'
    FIXED = 'F'
    DISCOUNT_TYPE_CHOICES = [
        (PERCENTAGE, 'Percentage'),
        (FIXED, 'Fixed Amount'),
    ]

    section = models.ForeignKey(
        'Section', on_delete=models.SET_NULL, blank=True, null=True)
    item = models.ForeignKey(
        'StoreItems', on_delete=models.SET_NULL, blank=True, null=True)
    discount_type = models.CharField(
        max_length=1, choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.FloatField(null=False)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    def calculate_new_price(self, original_price):
        # Assuming timezone.now() returns the correct current time.
        now = timezone.now()

        # Check if the discount is active by comparing dates.
        if self.start_date <= now <= self.end_date:
            if self.discount_type == self.PERCENTAGE:
                return original_price * (100 - self.discount_value) / 100
            elif self.discount_type == self.FIXED:
                return max(original_price - self.discount_value, 0)
        else:
            pass

        return original_price

    def __str__(self):
        return f"{'Section' if self.section else 'Item'} ItemDiscount"
