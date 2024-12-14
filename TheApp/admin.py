from django.contrib import admin
from nested_admin import NestedTabularInline, NestedModelAdmin
from .models import StoreItems, Section, Color, Tag, Discount, Variation, ItemVariation, StoreItemImage, Choices

# Inlines


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
    list_display = ['name']


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


# Registering models with their admins
admin.site.register(StoreItems, StoreItemAdmin)
admin.site.register(Section, SectionAdmin)
admin.site.register(Color, ColorAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Discount, DiscountAdmin)
admin.site.register(Variation, VariationAdmin)
admin.site.register(ItemVariation, ItemVariationAdmin)
admin.site.register(StoreItemImage, StoreItemImageAdmin)
