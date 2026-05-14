"""
Order creation + Stripe Checkout entry-point views.
"""

from __future__ import annotations

import json
import logging
from decimal import Decimal, InvalidOperation

import stripe
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from cart.cart import Cart
from cart.forms import CartAddProductForm
from TheApp.models import StoreItems

from .forms import OrderCreateForm
from .models import Order, OrderItem

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY


def _to_decimal(value) -> Decimal:
    try:
        return Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal("0.00")


@login_required
def order_create(request):
    cart = Cart(request)
    total_price = cart.get_total_price()

    # Annotate cart items for display (preserves existing template logic).
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

    cart_product_form = CartAddProductForm()

    if request.method == "POST":
        # If a valid unpaid order already exists in the session, reuse it
        # (back-button replay protection).
        existing_order_id = request.session.get("order_id")
        if existing_order_id:
            try:
                existing_order = Order.objects.get(
                    id=existing_order_id, paid=False, user=request.user
                )
                if existing_order.items.exists():
                    return redirect("orders:checkout_summary")
            except Order.DoesNotExist:
                pass

        form = OrderCreateForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                order = form.save(commit=False)
                order.user = request.user
                order.email = request.user.email or form.cleaned_data.get("email", "")
                order.save()

                product_ids = [data["item_id"] for data in cart.cart.values()]
                products_by_id = {
                    p.id: p for p in StoreItems.objects.filter(id__in=product_ids)
                }
                for _, item in cart.cart.items():
                    storeitem = products_by_id.get(item["item_id"])
                    if storeitem is None:
                        # The product was deleted between cart and checkout.
                        continue
                    variation_data = item.get("variation_choices", [])
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

                    OrderItem.objects.create(
                        order=order,
                        storeitem=storeitem,
                        item_name_snapshot=storeitem.item_name,
                        item_photo_url_snapshot=(
                            storeitem.item_photo.url if storeitem.item_photo else ""
                        ),
                        item_price=_to_decimal(item["item_price"]),
                        quantity=item["quantity"],
                        variations=variations,
                        choices=choices,
                    )

                cart.clear()
                request.session["order_id"] = order.id

            return redirect("orders:checkout_summary")
    else:
        request.session.pop("order_id", None)
        form = OrderCreateForm(initial={"email": request.user.email or ""})

    return render(
        request,
        "create.html",
        {
            "cart": cart,
            "form": form,
            "total_price": total_price,
            "cart_product_form": cart_product_form,
        },
    )


@login_required
def checkout_summary(request):
    order_id = request.session.get("order_id")
    if not order_id:
        messages.error(
            request,
            "Your checkout session expired before payment could start. "
            "Please submit your delivery details again.",
        )
        return redirect("orders:order_create")

    order = get_object_or_404(Order, id=order_id, user=request.user)

    if not order.items.exists():
        messages.error(request, "Your order has no items. Please go back and try again.")
        return redirect("orders:order_create")

    line_items = []
    for item in order.items.all().select_related("storeitem"):
        unit_amount = int(item.get_unit_price() * 100)
        line_items.append({
            "price_data": {
                "currency": "usd",
                "unit_amount": unit_amount,
                "product_data": {
                    "name": item.item_name_snapshot or (
                        item.storeitem.item_name if item.storeitem_id else f"Item #{item.id}"
                    ),
                },
            },
            "quantity": item.quantity,
        })

    session = stripe.checkout.Session.create(
        mode="payment",
        client_reference_id=str(order.id),
        metadata={"order_id": str(order.id)},
        success_url=request.build_absolute_uri(reverse("payment:completed")),
        cancel_url=request.build_absolute_uri(reverse("payment:canceled")),
        line_items=line_items,
    )
    return redirect(session.url, code=303)


@staff_member_required
def admin_order_detail(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related("items", "items__storeitem"),
        id=order_id,
    )
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
    return render(request, "admin/orders/order/detail.html", {"order": order})
