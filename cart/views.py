from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from TheApp.models import *
from .cart import Cart
from .forms import *
from django.core.serializers import serialize
from django.contrib import messages


@require_POST
def cart_add(request, item_id):
    cart = Cart(request)
    item = get_object_or_404(StoreItems, id=item_id)
    form = CartAddProductForm(request.POST, item=item)

    if form.is_valid():
        cd = form.cleaned_data
        variation_name = cd.get('variation')
        choice_name = cd.get('choice')
        quantity = cd['quantity']
        personalization = cd.get('personalization')
        override_quantity = cd.get('override')
        variation = Variation.objects.filter(
            name=variation_name).first() if variation_name else None
        choice = Choices.objects.filter(
            variation__item=item, name=choice_name).first() if choice_name and variation else None

        cart.add(
            item=item,
            quantity=quantity,
            variation=variation,
            choice=choice,
            personalization=personalization,
            override_quantity=override_quantity
        )
    return redirect('cart:cart_detail')


@require_POST
def cart_remove(request, item_id, variation_id=None):
    cart = Cart(request)
    item = get_object_or_404(StoreItems, id=item_id)
    variation = get_object_or_404(
        Variation, id=variation_id) if variation_id else None
    cart.remove(item, variation=variation)
    return redirect('cart:cart_detail')


def cart_detail(request):
    cart = Cart(request)
    original_length = len(cart.cart)
    total_price = cart.get_total_price()  # This will remove deleted items
    if len(cart.cart) < original_length:
        messages.warning(
            request, "Some items were removed from your cart because they are no longer available.")
    cart_product_form = CartAddProductForm()
    return render(request, "cart/detail.html", {
        "cart": cart,
        "total_price": total_price,
        "cart_product_form": cart_product_form
    })
