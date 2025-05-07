from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from TheApp.models import *
from .cart import Cart
from .forms import CartAddProductForm
from django.contrib import messages
from django.core.serializers import serialize


@require_POST
def cart_add(request, item_id):
    cart = Cart(request)
    item = get_object_or_404(StoreItems, id=item_id)
    form = CartAddProductForm(request.POST, item=item)

    if form.is_valid():
        cd = form.cleaned_data
        quantity = cd['quantity']
        personalization = cd.get('personalization')
        override = cd['override']

        variation_choice_list = []


        for key, value in request.POST.items():
            if key.startswith('variation_') and value:
                try:
                    choice_id = int(value)
                    choice = Choices.objects.select_related(
                        'variation').get(id=choice_id)
                    variation_choice_list.append({
                        'variation_name': choice.variation.variation.name,  # e.g., Color
                        'choice_name': choice.name,                         # e.g., Black
                        'price_increment': choice.price_increment or 0.0
                    })
                except (ValueError, Choices.DoesNotExist):
                    pass


        cart.add(
            item=item,
            quantity=quantity,
            variation_choice_list=variation_choice_list,
            personalization=personalization,
            override_quantity=override
        )


    return redirect('cart:cart_detail')


@require_POST
@require_POST
def cart_remove(request, item_id):
    print("REMOVE TRIGGERED:", item_id)
    cart = Cart(request)
    cart.remove(item_id)
    return redirect('cart:cart_detail')



def cart_detail(request):
    cart = Cart(request)
    original_length = len(cart.cart)
    total_price = cart.get_total_price()  # This will remove deleted items
    if len(cart.cart) < original_length:
        messages.warning(
            request, "Some items were removed from your cart because they are no longer available.")
    cart_product_form = CartAddProductForm()

    # Calculate discount percentages for each item
    for item in cart:
        if float(item['item_price']) > 0:  # Avoid division by zero
            discount = ((float(
                item['item_price']) - float(item['final_price'])) / float(item['item_price'])) * 100
            item['discount_percent'] = round(discount)
    
    return render(request, "cart/detail.html", {
        "cart": cart,
        "total_price": total_price,
        "cart_product_form": cart_product_form,
    })
