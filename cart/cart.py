from decimal import Decimal
from django.conf import settings
from TheApp.models import StoreItems, Choices


class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def save(self):
        self.session.modified = True

    def add(self, item, quantity=1, variation_choice_list=None, personalization=None, override_quantity=False, variation_key=None, variation_keys=None):
        variation_choice_list = variation_choice_list or []

        # Generate unique cart item ID based on item + choices
        variation_key = "-".join(
            [f"{c['variation_name']}:{c['choice_name']}" for c in variation_choice_list])
        cart_item_id = f"{item.id}--{variation_key}" if variation_key else str(
            item.id)

        base_price = float(item.get_final_price())
        extra_price = sum(float(c.get('price_increment', 0))
                          for c in variation_choice_list)
        final_price = base_price + extra_price

        if cart_item_id not in self.cart:
            self.cart[cart_item_id] = {
                'item_id': item.id,
                'quantity': 0,
                'item_price': str(item.item_price),
                'item_name': item.item_name,
                'item_description': item.item_description,
                'item_photo': item.item_photo.url if item.item_photo else '',
                'personalization': personalization,
                'variation_choices': variation_choice_list,
                'variation_key': variation_keys if variation_keys else None,

            }

        if override_quantity:
            self.cart[cart_item_id]['quantity'] = quantity
        else:
            self.cart[cart_item_id]['quantity'] += quantity

        self.save()

    def remove(self, item_id):
        item_id = str(item_id)
    
        for key in list(self.cart.keys()):
            if key.startswith(item_id):
                del self.cart[key]
                self.save()
                break





    def __iter__(self):
        cart_items_to_remove = []
        for cart_item_id, data in self.cart.items():
            try:
                item = StoreItems.objects.get(id=data['item_id'])
                quantity = data['quantity']
                base_price = float(item.get_final_price())

                variation_choices = data.get('variation_choices', [])
                extra_price = sum(float(vc.get('price_increment', 0))
                                  for vc in variation_choices)

                final_price = base_price + extra_price
                total_price = final_price * quantity

                yield {
                    'item_id': item.id,
                    'item_name': item.item_name,
                    'item_photo': item.item_photo.url if item.item_photo else '',
                    'quantity': quantity,
                    'item_price': base_price,
                    'final_price': final_price,  # ← THIS LINE FIXES YOUR ISSUE
                    'discount_percent': item.get_discount_percent() if hasattr(item, 'get_discount_percent') else 0,
                    'total_price': total_price,
                    'variation_choices': variation_choices,
                    'personalization': data.get('personalization', ''),
                }
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
        for data in self.cart.values():
            try:
                item = StoreItems.objects.get(id=data['item_id'])
                base_price = float(item.get_final_price())
                extra_price = sum(float(vc.get('price_increment', 0))
                                  for vc in data.get('variation_choices', []))
                total += (base_price + extra_price) * data['quantity']
            except StoreItems.DoesNotExist:
                continue
        return total

    def clear(self):
        self.session[settings.CART_SESSION_ID] = {}
        self.save()
