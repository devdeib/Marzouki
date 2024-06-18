from decimal import Decimal
import stripe
from django.conf import settings
from django.shortcuts import render, redirect, reverse, \
    get_object_or_404
from orders.models import Order
from cart.cart import Cart


def payment_process(request):
    order_id = request.session.get('order_id', None)
    order = get_object_or_404(Order, id=order_id)

    if request.method == 'POST':
        success_url = request.build_absolute_uri(reverse('payment:completed'))
        cancel_url = request.build_absolute_uri(reverse('payment:canceled'))
        # Stripe checkout session data
        session_data = {
            'mode': 'payment',
            'client_reference_id': order.id,
            'success_url': success_url,
            'cancel_url': cancel_url,
            'line_items': []
        }
        cart = Cart(request)
        cart.clear()
        request.session.save()
        # add order items to the Stripe checkout session
        for item in order.items.all():
            session_data['line_items'].append({
                'price_data': {
                    'unit_amount': int(item.item_price * Decimal('100')),
                    'currency': 'usd',
                    'product_data': {
                        'name': item.storeitem,
                    },
                },
                'quantity': item.quantity,
            })
        # create Stripe checkout session
        session = stripe.checkout.Session.create(**session_data)
        # redirect to Stripe payment form
        return redirect(session.url, code=303)

    else:
        return render(request, 'process.html', locals())


def payment_completed(request):
    order_id = request.session.get('order_id')
    if order_id:
        # Clearing the cart here ensures it is only cleared after successful payment.
        cart = Cart(request)
        cart.clear()
        # Ensure the session is saved after clearing the cart.
        request.session.save()

        # Clear the session's order_id to indicate the process is complete.
        del request.session['order_id']
        request.session.save()

        Order.objects.filter(id=order_id).update(paid=True)

        return render(request, 'completed.html', {'order_id': order_id})



def payment_canceled(request):
    return render(request, 'canceled.html')
