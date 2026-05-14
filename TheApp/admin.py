from django.contrib import admin
from nested_admin import NestedTabularInline, NestedModelAdmin
from .models import (
    StoreItems, Section, Color, Tag, Discount, Variation,
    ItemVariation, StoreItemImage, Choices, NewsletterSubscriber, ArtistProfile
)

class ItemImageInline(NestedTabularInline):
    model = StoreItemImage
    extra = 1


class ItemDiscountInLine(admin.TabularInline):
    model = Discount


class ChoiceInline(NestedTabularInline):
    model = Choices
    extra = 0


class ItemVariationInline(NestedTabularInline):
    model = ItemVariation
    inlines = [ChoiceInline, ]
    extra = 0

# Admin configurations


class StoreItemAdmin(NestedModelAdmin):
    list_display = ['item_name', 'item_price',
                    'item_status', 'item_quantity', 'created', 'updated']
    inlines = [ItemImageInline, ItemVariationInline]


class SectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    list_filter = ('category',)


class VariationAdmin(admin.ModelAdmin):
    list_display = ['name']


class ItemVariationAdmin(admin.ModelAdmin):
    list_display = ('item', 'variation')
    inlines = [ChoiceInline]


class ColorAdmin(admin.ModelAdmin):
    list_display = ['name', 'hex_value']


class TagAdmin(admin.ModelAdmin):
    list_display = ['name']


class DiscountAdmin(admin.ModelAdmin):
    list_display = ['section', 'item', 'discount_type',
                    'discount_value', 'start_date', 'end_date']


class StoreItemImageAdmin(admin.ModelAdmin):
    list_display = ['item']


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'subscribed_at', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('email',)
    actions = ['send_newsletter']

    def send_newsletter(self, request, queryset):
        # Only send to active subscribers
        active_subscribers = queryset.filter(is_active=True)
        if not active_subscribers:
            self.message_user(request, "No active subscribers selected.")
            return

        # For this simple example, we'll hardcode the subject and message
        # You could extend this with a form to input these dynamically
        subject = "Weekly Newsletter from Paint Store"
        message = "Hello,\n\nHere’s your weekly update from the Paint Store!\nStay tuned for new products and offers.\n\nBest,\nThe Paint Store Team"
        from_email = 'your-email@gmail.com'  # Match DEFAULT_FROM_EMAIL

        # Prepare email tuples for send_mass_mail
        emails = [
            (subject, message, from_email, [subscriber.email])
            for subscriber in active_subscribers
        ]

        try:
            send_mass_mail(emails, fail_silently=False)
            self.message_user(
                request, f"Newsletter sent to {len(emails)} subscribers.")
        except Exception as e:
            self.message_user(
                request, f"Error sending newsletter: {str(e)}", level='error')

    send_newsletter.short_description = "Send newsletter to selected subscribers"
    
    
@admin.register(ArtistProfile)
class ArtistProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('bio', 'photo'),
        }),
    )

    def has_add_permission(self, request):
        # Prevent adding more than one instance
        return not ArtistProfile.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of the singleton instance
        return False

# Registering models with their admins
admin.site.register(StoreItems, StoreItemAdmin)
admin.site.register(Section, SectionAdmin)
admin.site.register(Color, ColorAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Discount, DiscountAdmin)
admin.site.register(Variation, VariationAdmin)
admin.site.register(ItemVariation, ItemVariationAdmin)
admin.site.register(StoreItemImage, StoreItemImageAdmin)
