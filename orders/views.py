from django.urls import reverse
from django.shortcuts import render, redirect
from .models import OrderItem
from .forms import OrderCreateForm
from cart.cart import Cart
from .tasks import order_created
from django.http import JsonResponse
from TheApp.models import StoreItems
from django.core.serializers import serialize
from django.db import transaction
from django.contrib import messages


def order_create(request):
    cart = Cart(request)
    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save()
            for cart_item_id, item in cart.cart.items():
                storeitem = StoreItems.objects.get(id=item['item_id'])
                OrderItem.objects.create(
                    order=order,
                    storeitem=storeitem,
                    item_price=item['item_price'],
                    quantity=item['quantity']
                )

            
            # clear the cart
            cart.clear()
            print("cleard")
            request.session.save()
            # set the order in the session
            request.session['order_id'] = order.id
            # redirect for payment
            return redirect(reverse('payment:process'))

    else:
        form = OrderCreateForm()
    return render(request, 'create.html', {'cart': cart, 'form': form})
