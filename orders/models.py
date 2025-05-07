from decimal import Decimal
from django.db import models
from TheApp.models import *
from django.conf import settings
from django.db.models import JSONField

class Order(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    address = models.CharField(max_length=250)
    postal_code = models.CharField(max_length=20)
    city = models.CharField(max_length=100)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    paid = models.BooleanField(default=False)
    stripe_id = models.CharField(max_length=250, blank=True)

    class Meta:
        ordering = ['-created']
        indexes = [models.Index(fields=['-created'])]

    def __str__(self):
        return f'Order {self.id}'

    def get_total_cost(self):
        return sum(item.get_cost() for item in self.items.all())

    def get_stripe_url(self):
        if not self.stripe_id:
            return ''
        if '_test_' in settings.STRIPE_SECRET_KEY:
            path = '/test/'
        else:
            path = '/'
        return f'https://dashboard.stripe.com{path}payments/{self.stripe_id}'


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, related_name='items', on_delete=models.CASCADE)
    storeitem = models.ForeignKey(
        StoreItems, related_name='order_items', on_delete=models.CASCADE)
    item_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    # <-- holds list of variation dicts
    variations = JSONField(blank=True, null=True)
    # <-- holds list of choice dicts
    choices = models.JSONField(default=list, blank=True)

    @property
    def choice_increment(self):
        # assuming only one choice per item
        if self.choices and isinstance(self.choices, list):
            return self.choices[0].get("price", 0)
        return 0


    def get_cost(self):
        base = self.item_price
        choice_total = sum(Decimal(str(c.get('increment', 0)))
                           for c in self.choices or [])
        return (base + choice_total) * self.quantity

    @property
    def choices_list(self):
        try:
            return self.choices if isinstance(self.choices, list) else []
        except:
            return []
    
    
    @property
    def variations_list(self):
        try:
            return self.variations if isinstance(self.variations, list) else []
        except:
            return []
