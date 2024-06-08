from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from TheApp.models import *
from .cart import Cart
from .forms import *


@require_POST
def cart_add(request, item_id):
    cart = Cart(request)
    item = get_object_or_404(StoreItems, id=item_id)
    if request.method == 'POST':
        form = CartAddProductForm(request.POST, item=item)

        if form.is_valid():
            cd = form.cleaned_data
            variation_name = cd.get('variation')
            choice_name = cd.get('choice')
            quantity = cd['quantity']
            personalization = cd.get('personalization')
            override_quantity = cd.get('override')
            variation_object = None
            choice_object = None
            new_price = item.item_price

            if variation_name:
                variation_object = get_object_or_404(
                    Variation, name=variation_name)
                item_variation = get_object_or_404(
                    ItemVariation, item=item, variation=variation_object)

                if choice_name:
                    choice_object = get_object_or_404(
                        Choices, variation=item_variation, name=choice_name)
                    new_price += choice_object.price_increment

                # Add item to the cart with variation and choice
                cart.add(item=item, quantity=quantity, variation=variation_object, choice=choice_object,
                         price=new_price, personalization=personalization, override_quantity=override_quantity)
            else:
                print("helooooooooooooooooooooooooooooooooooooooooooo")
                # Add item to the cart without variation
                cart.add(item=item, quantity=quantity, personalization=personalization,
                         price=new_price, override_quantity=override_quantity)

            if override_quantity:
                cart.set_quantity(item=item, quantity=quantity, variation=variation_object,
                                  choice=choice_object, personalization=personalization)

    return redirect('cart:cart_detail')




@require_POST
def cart_remove(request, item_id, variation_id=None):
    cart_item_id = Cart(request)
    item = get_object_or_404(StoreItems, id=item_id)
    # Replace variationVariant with your actual variation model
    variation = get_object_or_404(
        Variation, id=variation_id) if variation_id else None

    cart_item_id.remove(item, variation=variation)

    return redirect('cart:cart_detail')


def cart_detail(request):
    cart = Cart(request)
    total_price = cart.get_total_price()  # Call the method to get the total price
    cart_product_form = CartAddProductForm()

    for item_id, item_data in cart.cart.items():
        # Split the cart_item_id to get the original item_id and size_id
        item_id_parts = item_id.split('-')
        # This extracts the item_id only without the size_id
        original_item_id = item_id_parts[0]
        # Assign the original item_id to the item_data for URL reversing
        item_data['id'] = original_item_id

        variation_name = item_data.get('variation')
        item_data['variation'] = variation_name  # Use the size name directly
        
        choice_name = item_data.get('choice')
        item_data['choice'] = choice_name  # Use the size name directly

    cart.save()  # No need to save the cart just because we accessed it, but this does not hurt

    return render(request, "cart/detail.html", {
        "cart": cart,
        "total_price": total_price,
        "cart_product_form": cart_product_form
    })
