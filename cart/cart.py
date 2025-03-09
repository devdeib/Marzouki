from decimal import Decimal
from django.conf import settings
from TheApp.models import StoreItems, Choices  # Add Choices here


class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def save(self):
        self.session.modified = True

    def add(self, item, quantity=1, variation=None, choice=None, personalization=None, price=None, override_quantity=False):
        variation_part = f'-{str(variation.id)}' if variation else ''
        choice_part = f'-{str(choice.id)}' if choice else ''
        cart_item_id = f'{item.id}{variation_part}{choice_part}'
        variation_name = variation.name if variation else None
        choice_name = choice.name if choice else None

        base_price = float(item.get_final_price())
        final_price = base_price
        if choice and choice.price_increment:
            final_price += float(choice.price_increment)

        if cart_item_id not in self.cart:
            self.cart[cart_item_id] = {
                'item_id': item.id,
                'quantity': 0,
                'item_price': str(item.item_price),
                'final_price': str(final_price),
                'item_name': item.item_name,
                'item_description': item.item_description,
                'item_photo': item.item_photo.url if item.item_photo else None,
                'variation': variation_name,
                'choice': choice_name,
                'personalization': personalization,
                'choice_increment': str(choice.price_increment) if choice and choice.price_increment else '0',
            }

        if override_quantity:
            self.cart[cart_item_id]['quantity'] = quantity
        else:
            self.cart[cart_item_id]['quantity'] += quantity

        self.save()

    def remove(self, item, variation=None):
        variation_part = f'-{str(variation.id)}' if variation else ''
        cart_item_id = f'{item.id}{variation_part}'
        if cart_item_id in self.cart:
            del self.cart[cart_item_id]
            self.save()

    def __iter__(self):
        cart_items_to_remove = []
        for cart_item_id, item_data in self.cart.items():
            try:
                item = StoreItems.objects.get(id=item_data['item_id'])
                final_price = float(item.get_final_price())
                if item_data['choice']:
                    choice = Choices.objects.filter(
                        variation__item=item, name=item_data['choice']).first()
                    if choice and choice.price_increment:
                        final_price += float(choice.price_increment)
                item_data['final_price'] = final_price
                item_data['total_price'] = final_price * item_data['quantity']
                yield item_data
            except StoreItems.DoesNotExist:
                cart_items_to_remove.append(cart_item_id)

        for item_id in cart_items_to_remove:
            del self.cart[item_id]
        if cart_items_to_remove:
            self.save()

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        total = 0
        cart_items_to_remove = []
        for item_data in self.cart.values():
            try:
                item = StoreItems.objects.get(id=item_data['item_id'])
                final_price = float(item.get_final_price())
                if item_data['choice']:
                    choice = Choices.objects.filter(
                        variation__item=item, name=item_data['choice']).first()
                    if choice and choice.price_increment:
                        final_price += float(choice.price_increment)
                total += final_price * item_data['quantity']
            except StoreItems.DoesNotExist:
                cart_items_to_remove.append(item_data['item_id'])

        for item_id in cart_items_to_remove:
            cart_item_id = next(
                (key for key, value in self.cart.items() if value['item_id'] == item_id), None)
            if cart_item_id:
                del self.cart[cart_item_id]
        if cart_items_to_remove:
            self.save()

        return total

    def clear(self):
        del self.session[settings.CART_SESSION_ID]
        self.save()

    def update_item(self, item_id, item_data):
        if item_id in self.cart:
            self.cart[item_id].update(item_data)
            self.save()
