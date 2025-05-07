from django.utils.safestring import mark_safe
import json
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from .models import OrderItem, Order
from .forms import OrderCreateForm
from cart.cart import Cart
from django.http import JsonResponse
from TheApp.models import StoreItems
from django.core.serializers import serialize
from django.db import transaction
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required


def order_create(request):
    cart = Cart(request)
    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save()
            for cart_item_id, item in cart.cart.items():
                storeitem = StoreItems.objects.get(id=item['item_id'])

                # Get variation choices from cart
                variation_data = item.get('variation_choices', [])

                # Split into two structures: variations + choices
                variations = [
                    {"name": v["variation_name"], "value": v["choice_name"]}
                    for v in variation_data
                ]
                choices = [
                    {
                        "variation": v["variation_name"],
                        "choice": v["choice_name"],
                        "increment": float(v.get("price_increment", 0)),
                    }
                    for v in variation_data
                ]

                # Create the order item
                OrderItem.objects.create(
                    order=order,
                    storeitem=storeitem,
                    item_price=item['item_price'],
                    quantity=item['quantity'],
                    variations=variations,
                    choices=choices
                )

            cart.clear()
            request.session.save()
            request.session['order_id'] = order.id
            return redirect(reverse('payment:process'))
    else:
        form = OrderCreateForm()
    return render(request, 'create.html', {'cart': cart, 'form': form})


@staff_member_required
def admin_order_detail(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related('items'), id=order_id)

    for item in order.items.all():
        if isinstance(item.choices, str):
            try:
                item.choices = json.loads(item.choices)
            except json.JSONDecodeError:
                item.choices = []

        if isinstance(item.variations, str):
            try:
                item.variations = json.loads(item.variations)
            except json.JSONDecodeError:
                item.variations = []

    return render(request, 'admin/orders/order/detail.html', {'order': order})
