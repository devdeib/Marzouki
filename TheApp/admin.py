from django.contrib import admin
from .models import *
from nested_admin import NestedTabularInline, NestedModelAdmin

# Inlines


class ItemImageInline(admin.TabularInline):
    model = StoreItemImage
    extra = 1  # Number of empty extra forms


class ItemDiscountInLine(admin.TabularInline):
    model = Discount


class ChoiceInline(NestedTabularInline):
    model = Choices
    extra = 0  # No extra rows by default
    # Add 'fk_name' if 'Choice' has multiple foreign keys to 'Variation'


class ItemVariationInline(NestedTabularInline):
    model = ItemVariation
    inlines = [ChoiceInline, ]
    extra = 0  # No extra rows by default


# Admin configurations
class StoreItemAdmin(NestedModelAdmin):
    list_display = ['item_name', 'item_price',
                    'item_status', 'item_quantity', 'created', 'updated']
    inlines = [ItemVariationInline]
    # Other admin configurations, if needed


class SectionAdmin(admin.ModelAdmin):
    list_display = ['name']
    # If you want to show items from a section, you can use inlines, but since it's a ForeignKey relation in StoreItems, it's not required here


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
    inlines = [
        ItemImageInline,
    ]


# Registering models with their admins
admin.site.register(StoreItems, StoreItemAdmin)
admin.site.register(Section, SectionAdmin)
admin.site.register(Color, ColorAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Discount, DiscountAdmin)
# Assuming you don't need a custom admin for this model
admin.site.register(Variation, VariationAdmin)
admin.site.register(ItemVariation, ItemVariationAdmin)
