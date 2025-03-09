from decimal import Decimal
import stripe
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from orders.models import Order
from cart.cart import Cart
from django.urls import reverse


def payment_process(request):
    order_id = request.session.get('order_id', None)
    order = get_object_or_404(Order, id=order_id)

    if request.method == 'POST':
        session_data = {
            'mode': 'payment',
            'client_reference_id': order.id,
            'success_url': request.build_absolute_uri(reverse('payment:completed')),
            'cancel_url': request.build_absolute_uri(reverse('payment:canceled')),
            'line_items': []
        }

        for item in order.items.all():
            # Calculate the final price including choice increment
            final_price = item.item_price + item.choice_increment
            session_data['line_items'].append({
                'price_data': {
                    # Convert to cents
                    'unit_amount': int(final_price * Decimal('100')),
                    'currency': 'usd',
                    'product_data': {
                        'name': item.storeitem.item_name,
                    },
                },
                'quantity': item.quantity,
            })

        session = stripe.checkout.Session.create(**session_data)
        return redirect(session.url, code=303)

    return render(request, 'process.html', locals())


def payment_completed(request):
    order_id = request.session.get('order_id')
    if order_id:
        cart = Cart(request)
        cart.clear()
        request.session.save()
        del request.session['order_id']
        request.session.save()
        Order.objects.filter(id=order_id).update(paid=True)
        return render(request, 'completed.html', {'order_id': order_id})


def payment_canceled(request):
    return render(request, 'canceled.html')
