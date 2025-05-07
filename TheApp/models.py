from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import FileExtensionValidator
# Create your models here


class UserProfile(models.Model):

    user = models.OneToOneField(
        User, null=True, blank=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, null=True)
    email = models.CharField(max_length=200, null=True)
    photo = models.ImageField(
        upload_to='media/profile_photos/', default="default.webp", null=True, blank=True)

    def __str__(self):
        return self.user.username  # Helps to see the associated user profile

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

    def __str__(self):  # Changed from str to __str__
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
    item_quantity = models.IntegerField(default=0)
    variations = models.ManyToManyField('Variation', through='ItemVariation')
    created = models.DateTimeField(auto_now=True)
    updated = models.DateTimeField(auto_now=True)
    tags = models.ManyToManyField('Tag', blank=True)
    primary_color = models.ForeignKey(
        'Color', related_name='primary_color_items', blank=True, null=True, on_delete=models.SET_NULL)
    secondary_color = models.ForeignKey(
        'Color', related_name='secondary_color_items', blank=True, null=True, on_delete=models.SET_NULL)
    video = models.FileField(upload_to='items_videos/', null=True, blank=True)
    width = models.FloatField(null=True, blank=True)
    height = models.FloatField(null=True, blank=True)

    def get_final_price(self):
        """Return the final price after applying any active discount."""
        now = timezone.now()
        # Check for item-specific discount
        current_discount = self.discount_set.filter(
            start_date__lte=now,
            end_date__gte=now
        ).first()

        if current_discount:
            return current_discount.calculate_new_price(self.item_price)

        # Check for section discount
        section_discount = Discount.objects.filter(
            section__in=self.section.all(),
            start_date__lte=now,
            end_date__gte=now
        ).first()

        if section_discount:
            return section_discount.calculate_new_price(self.item_price)

        # No active discount, return original price
        return self.item_price

    def __str__(self):  # Changed from str to __str__
        return self.item_name

class StoreItemImage(models.Model):
    item = models.ForeignKey(
        StoreItems, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='items_media/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.item.item_name} Image"


class StoreItemVideo(models.Model):
    item = models.ForeignKey(
        StoreItems, related_name='videos', on_delete=models.CASCADE)
    video_file = models.FileField(upload_to='items_videos/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.item.item_name} Video"


class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)  # Ensure no duplicate subscriptions
    subscribed_at = models.DateTimeField(
        auto_now_add=True)  # Timestamp of subscription
    is_active = models.BooleanField(default=True)  # Allow unsubscribing

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = "Newsletter Subscriber"
        verbose_name_plural = "Newsletter Subscribers"

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
    item = models.ForeignKey(
        StoreItems,
        on_delete=models.CASCADE,
        related_name='item_variations'  # Add this explicit related_name
    )
    variation = models.ForeignKey(Variation, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.item.item_name} - {self.variation.name}"

    class Meta:
        verbose_name_plural = "Item Variations"


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
        """Calculate the discounted price based on the discount type and value."""
        now = timezone.now()

        # Check if the discount is active
        if self.start_date <= now <= self.end_date:
            if self.discount_type == self.PERCENTAGE:
                return original_price * (100 - self.discount_value) / 100
            elif self.discount_type == self.FIXED:
                return max(original_price - self.discount_value, 0)

        # If the discount is not active, return the original price
        return original_price

    def __str__(self):
        return f"{'Section' if self.section else 'Item'} Discount: {self.discount_value} ({self.get_discount_type_display()})"


class ArtistProfile(models.Model):
    bio = models.TextField(blank=True, )
    photo = models.ImageField(
        upload_to='artist_photos/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(
            allowed_extensions=['jpg', 'jpeg', 'png'])],
    
    
    )
    updated_at = models.DateTimeField(auto_now=True)
    # Social profile fields
    twitter_url = models.URLField(blank=True, default='')
    twitter_show = models.BooleanField(default=False)
    instagram_url = models.URLField(blank=True, default='')
    instagram_show = models.BooleanField(default=False)
    facebook_url = models.URLField(blank=True, default='')
    facebook_show = models.BooleanField(default=False)
    class Meta:
        verbose_name = "Artist Profile"
        verbose_name_plural = "Artist Profile"

    def __str__(self):
        return "Artist Profile"

    @classmethod
    def get_solo(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj
