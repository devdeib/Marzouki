from django.contrib import admin
from .models import Order, OrderItem
from django.utils.safestring import mark_safe
from django.urls import reverse


from django.contrib import admin
from .models import Order, OrderItem
from django.utils.safestring import mark_safe
from django.urls import reverse


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['storeitem']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'first_name', 'last_name', 'email',
                    'address', 'postal_code', 'city', 'paid',
                    'order_payment_display', 'created', 'updated', 'order_detail']
    list_filter = ['paid', 'created', 'updated']
    inlines = [OrderItemInline]

    def order_payment_display(self, obj):
        url = obj.get_stripe_url()
        if obj.stripe_id:
            html = f'<a href="{url}" target="_blank">{obj.stripe_id}</a>'
            return mark_safe(html)
        return ''
    order_payment_display.short_description = 'Stripe payment'

    def order_detail(self, obj):
        url = reverse('orders:admin_order_detail', args=[obj.id])
        return mark_safe(f'<a href="{url}">View</a>')
    order_detail.short_description = 'Order Details'
