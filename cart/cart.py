from decimal import Decimal
from django.conf import settings
from TheApp.models import *


class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, item, quantity=1, variation=None, choice=None, personalization=None, price=None, override_quantity=False):
        variation_part = f'-{str(variation.id)}' if variation else ''
        choice_part = f'-{str(choice.id)}' if choice else ''
        cart_item_id = f'{item.id}{variation_part}{choice_part}'

        if cart_item_id not in self.cart:
            self.cart[cart_item_id] = {
                'item_id': item.id,
                'quantity': 0,
                'item_price': str(price if price else item.item_price),
                'item_name': item.item_name,
                'item_description': item.item_description,
                'item_photo': item.item_photo.url if item.item_photo else None,
                'variation': variation.name if variation else None,
                'choice': choice.name if choice else None,
                'personalization': personalization
            }

        if override_quantity:
            self.cart[cart_item_id]['quantity'] = quantity
        else:
            self.cart[cart_item_id]['quantity'] += quantity

        self.save()

    def save(self):
        self.session[settings.CART_SESSION_ID] = self.cart
        self.session.modified = True

    def remove(self, item, variation=None):
        """
        Remove an itezm from the cart.
        """
        variation_part = f'-{str(variation.id)}' if variation else ''
        cart_item_id = f'{item.id}{variation_part}'

        if cart_item_id in self.cart:
            del self.cart[cart_item_id]
            self.save()
        else:
            pass

    def __iter__(self):
        """
        Iterate over the items in the cart and get the items
        from the database.
        """
        cart_item_ids = self.cart.keys()
        # get the product objects and add them to the cart
        items = StoreItems.objects.filter(id__in=cart_item_ids)
        cart = self.cart.copy()
        for item in items:
            cart[str(item.id)]['item'] = item
        for item in cart.values():
            item['item_price'] = float(item['item_price'])
            item['total_price'] = float(item['item_price']) * item['quantity']
            yield item

    def __len__(self):
        """
        Count all items in the cart.
        """
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        return sum(float(item['item_price']) * item['quantity'] for item in self.
                   cart.values())

    def clear(self):
        # remove cart from session
        del self.session[settings.CART_SESSION_ID]
        self.save()
