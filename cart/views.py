"""
Session-cart views.
"""

from __future__ import annotations

import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from TheApp.models import Choices, StoreItems

from .cart import Cart
from .forms import CartAddProductForm

logger = logging.getLogger(__name__)


@require_POST
@login_required
def cart_add(request, item_id):
    cart = Cart(request)
    item = get_object_or_404(StoreItems, id=item_id)
    form = CartAddProductForm(request.POST, item=item)

    if form.is_valid():
        cd = form.cleaned_data
        quantity = cd["quantity"]
        personalization = cd.get("personalization")
        override = cd["override"]

        # Collect all variation_X choice IDs from the form, then look them
        # up in a single query to avoid N queries per cart add.
        choice_ids: list[int] = []
        for key, value in request.POST.items():
            if key.startswith("variation_") and value:
                try:
                    choice_ids.append(int(value))
                except ValueError:
                    continue

        variation_choice_list = []
        if choice_ids:
            choices = (
                Choices.objects.filter(id__in=choice_ids)
                .select_related("variation__variation")
            )
            for choice in choices:
                variation_choice_list.append({
                    "variation_name": choice.variation.variation.name,
                    "choice_name": choice.name,
                    "price_increment": float(choice.price_increment or 0.0),
                })

        cart.add(
            item=item,
            quantity=quantity,
            variation_choice_list=variation_choice_list,
            personalization=personalization,
            override_quantity=override,
        )

    return redirect("cart:cart_detail")


@require_POST
@login_required
def cart_remove(request, item_id):
    cart = Cart(request)
    cart.remove(item_id)
    return redirect("cart:cart_detail")


def cart_detail(request):
    cart = Cart(request)
    original_length = len(cart.cart)
    total_price = cart.get_total_price()
    if len(cart.cart) < original_length:
        messages.warning(
            request,
            "Some items were removed from your cart because they are no longer available.",
        )
    cart_product_form = CartAddProductForm()

    # Annotate per-item discount percent for display.
    for item in cart:
        try:
            base_price = float(item["item_price"])
            final_price = float(item["final_price"])
        except (TypeError, ValueError):
            base_price = final_price = 0.0
        if base_price > 0:
            discount = ((base_price - final_price) / base_price) * 100
            item["discount_percent"] = round(discount)
        else:
            item["discount_percent"] = 0

    return render(
        request,
        "cart/detail.html",
        {
            "cart": cart,
            "total_price": total_price,
            "cart_product_form": cart_product_form,
        },
    )


def terms_and_conditions(request):
    return render(request, "cart/terms_and_conditions.html")
