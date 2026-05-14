"""
Public-facing views for the catalog, auth, and informational pages.
"""

from __future__ import annotations

import logging
import os

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, logout
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.core.validators import FileExtensionValidator
from django.db.models import Prefetch, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from cart.forms import CartAddProductForm
from orders.models import Order

from .forms import (
    ArtistBioForm,
    ArtistPhotoForm,
    NewsletterSubscriptionForm,
    SignupForm,
    SocialProfilesForm,
)
from .models import (
    ArtistProfile,
    Choices,
    ItemVariation,
    NewsletterSubscriber,
    Section,
    StoreItemImage,
    StoreItems,
    StoreItemVideo,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
HERO_IMAGE_RELATIVE_PATH = "hero/hero.jpg"
HERO_IMAGE_MAX_BYTES = 5 * 1024 * 1024  # 5 MB
HERO_IMAGE_ALLOWED_EXTENSIONS = ("jpg", "jpeg", "png", "webp")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _paginate(request, queryset, per_page=12):
    paginator = Paginator(queryset, per_page)
    page = request.GET.get("page")
    try:
        return paginator.page(page)
    except PageNotAnInteger:
        return paginator.page(1)
    except EmptyPage:
        return paginator.page(paginator.num_pages)


# ---------------------------------------------------------------------------
# Error pages
# ---------------------------------------------------------------------------
def error_500(request, *args, **kwargs):
    # Standalone template — no DB lookups — so a 500 caused by DB outage
    # still renders cleanly.
    return render(request, "error.html", status=500)


def robots_txt(request):
    """Plain-text robots.txt with dynamic absolute sitemap URL."""
    scheme = "https" if request.is_secure() else request.scheme
    host = request.get_host()
    body = (
        "User-agent: *\n"
        "Allow: /\n"
        "\n"
        f"Sitemap: {scheme}://{host}/sitemap.xml\n"
    )
    return HttpResponse(body, content_type="text/plain")


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
def signup(request):
    if request.user.is_authenticated:
        return redirect("paints")

    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            if User.objects.filter(email__iexact=email).exists():
                return render(
                    request,
                    "signup.html",
                    {"form": form, "user_exists": True},
                )
            user = form.save()
            raw_password = form.cleaned_data.get("password1")
            auth_user = authenticate(username=user.username, password=raw_password)
            if auth_user:
                auth_login(request, auth_user)
            return redirect("paints")
    else:
        form = SignupForm()
    return render(request, "signup.html", {"form": form})


def login(request):
    if request.user.is_authenticated:
        return redirect("paints")

    error = None
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect("paints")
        error = "Invalid username or password."
    return render(request, "login.html", {"error": error})


@require_POST
@login_required
def user_logout(request):
    logout(request)
    return redirect("home")


@login_required
def account(request):
    orders = (
        Order.objects.filter(user=request.user)
        .prefetch_related("items", "items__storeitem")
        .order_by("-created")
    )
    return render(
        request,
        "account.html",
        {"user": request.user, "orders": orders},
    )


# ---------------------------------------------------------------------------
# Home
# ---------------------------------------------------------------------------
def _save_hero_image(uploaded_file) -> None:
    """Validate and write the new hero image to MEDIA_ROOT/hero/hero.jpg."""
    if uploaded_file.size > HERO_IMAGE_MAX_BYTES:
        raise ValidationError(
            f"Image too large ({uploaded_file.size} bytes). Max is {HERO_IMAGE_MAX_BYTES}."
        )
    FileExtensionValidator(allowed_extensions=list(HERO_IMAGE_ALLOWED_EXTENSIONS))(uploaded_file)

    hero_dir = os.path.join(settings.MEDIA_ROOT, "hero")
    os.makedirs(hero_dir, exist_ok=True)
    target = os.path.join(hero_dir, "hero.jpg")
    with open(target, "wb+") as destination:
        for chunk in uploaded_file.chunks():
            destination.write(chunk)


def home(request):
    subscription_form = NewsletterSubscriptionForm()
    hero_image_url = settings.MEDIA_URL + HERO_IMAGE_RELATIVE_PATH

    if request.method == "POST":
        if request.FILES.get("image"):
            if not (request.user.is_authenticated and request.user.is_superuser):
                return redirect("home")
            try:
                _save_hero_image(request.FILES["image"])
                messages.success(request, "Hero image updated.")
            except ValidationError as exc:
                messages.error(request, " ".join(exc.messages))
            except Exception as exc:  # noqa: BLE001
                logger.exception("Hero image save failed")
                messages.error(request, f"Could not save image: {exc}")
            return redirect("home")

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            form = NewsletterSubscriptionForm(request.POST)
            if form.is_valid():
                email = form.cleaned_data["email"]
                subscriber, created = NewsletterSubscriber.objects.get_or_create(email=email)
                if not created and not subscriber.is_active:
                    subscriber.is_active = True
                    subscriber.save(update_fields=["is_active"])
                return JsonResponse(
                    {"success": True, "message": "Thank you for subscribing!"}
                )
            errors = form.errors.as_data()
            error_message = "There was an issue with your subscription."
            if "email" in errors:
                for error in errors["email"]:
                    code = getattr(error, "code", None)
                    if code == "unique":
                        error_message = "This email is already subscribed."
                        break
                    if code == "invalid":
                        error_message = "Please enter a valid email address."
                        break
            return JsonResponse({"success": False, "message": error_message}, status=400)

    return render(
        request,
        "home.html",
        {"subscription_form": subscription_form, "hero_image_url": hero_image_url},
    )


# ---------------------------------------------------------------------------
# Catalog listings
# ---------------------------------------------------------------------------
def _catalog_queryset(extra_filter=None):
    """Base queryset for product listing pages with prefetches that match
    what the listing templates actually access."""
    qs = (
        StoreItems.objects.all()
        .select_related("primary_color", "secondary_color")
        .prefetch_related(
            "tags",
            "section",
            Prefetch("discount_set"),
        )
        .order_by("order")
    )
    if extra_filter is not None:
        qs = qs.filter(extra_filter)
    return qs


def paints(request):
    items = _catalog_queryset()
    page_obj = _paginate(request, items)
    return render(
        request,
        "paints.html",
        {
            "items": items,
            "itemss": page_obj,
            "on_paints_page": True,
        },
    )


def originals(request):
    items = (
        _catalog_queryset(extra_filter=Q(section__category="OR", status__in=["AC", "SO"]))
        .distinct()
    )
    page_obj = _paginate(request, items)
    return render(
        request,
        "originals.html",
        {
            "items": items,
            "itemss": page_obj,
            "on_originals_page": True,
        },
    )


def prints(request):
    items = (
        _catalog_queryset(extra_filter=Q(section__category="PR", status__in=["AC", "SO"]))
        .distinct()
    )
    page_obj = _paginate(request, items)
    return render(
        request,
        "prints.html",
        {
            "items": items,
            "itemss": page_obj,
            "on_prints_page": True,
        },
    )


def category_browse(request, section_id):
    section = get_object_or_404(Section, id=section_id)
    items = (
        section.items.all()
        .select_related("primary_color", "secondary_color")
        .prefetch_related("tags", "section")
        .order_by("order")
    )
    page_obj = _paginate(request, items)
    return render(
        request,
        "category_page.html",
        {
            "section": section,
            "items": items,
            "itemss": page_obj,
            "on_category_page": True,
            "on_paints_page": True,
        },
    )


def paint_detail(request, item_id):
    store_item = get_object_or_404(
        StoreItems.objects.select_related("primary_color", "secondary_color").prefetch_related(
            "tags", "section", "images", "videos", "item_variations__variation",
        ),
        pk=item_id,
    )

    items_sc = StoreItems.objects.filter(status="SC").order_by("order")
    next_item = items_sc.filter(order__gt=store_item.order).order_by("order").first()
    prev_item = items_sc.filter(order__lt=store_item.order).order_by("order").last()

    tags_of_item = store_item.tags.all()
    related_items = (
        StoreItems.objects.filter(tags__in=tags_of_item)
        .exclude(id=store_item.id)
        .select_related("primary_color")
        .distinct()
    )

    item_images = store_item.images.all()
    item_videos = store_item.videos.all()

    item_variations = store_item.item_variations.all().select_related("variation").prefetch_related("choices")
    variations_with_choices = [
        {"variation": iv.variation, "choices": iv.choices.all()}
        for iv in item_variations
    ]

    cart_product_form = CartAddProductForm(item=store_item)

    return render(
        request,
        "paint_detail.html",
        {
            "item": store_item,
            "variations_with_choices": variations_with_choices,
            "cart_product_form": cart_product_form,
            "related_items": related_items,
            "item_images": item_images,
            "item_videos": item_videos,
            "next_item": next_item,
            "prev_item": prev_item,
            "on_paints_page": True,
        },
    )


def search(request):
    query = request.GET.get("query", "").strip()[:200]  # cap length

    if query:
        results = (
            StoreItems.objects.filter(
                Q(item_name__icontains=query)
                | Q(tags__name__icontains=query)
                | Q(primary_color__name__icontains=query)
                | Q(secondary_color__name__icontains=query)
            )
            .select_related("primary_color", "secondary_color")
            .prefetch_related("tags")
            .distinct()
            .order_by("order")
        )
    else:
        results = StoreItems.objects.none()

    return render(
        request,
        "search_results.html",
        {
            "results": results,
            "query": query,
            "on_paints_page": True,
        },
    )


# ---------------------------------------------------------------------------
# About
# ---------------------------------------------------------------------------
def about(request):
    artist = ArtistProfile.get_solo()
    bio_form = ArtistBioForm(instance=artist)
    photo_form = ArtistPhotoForm(instance=artist)

    social_profiles = {
        "twitter": {"url": artist.twitter_url, "show": artist.twitter_show},
        "instagram": {"url": artist.instagram_url, "show": artist.instagram_show},
        "facebook": {"url": artist.facebook_url, "show": artist.facebook_show},
    }
    social_form = SocialProfilesForm(initial={
        "twitter_url": artist.twitter_url,
        "twitter_active": artist.twitter_show,
        "instagram_url": artist.instagram_url,
        "instagram_active": artist.instagram_show,
        "facebook_url": artist.facebook_url,
        "facebook_active": artist.facebook_show,
    })

    if request.method == "POST" and request.user.is_authenticated and request.user.is_superuser:
        if "bio_submit" in request.POST:
            bio_form = ArtistBioForm(request.POST, instance=artist)
            if bio_form.is_valid():
                bio_form.save()
                return redirect("about")
        elif "photo_submit" in request.POST:
            photo_form = ArtistPhotoForm(request.POST, request.FILES, instance=artist)
            if photo_form.is_valid():
                photo_form.save()
                return redirect("about")
        elif "social_submit" in request.POST:
            social_form = SocialProfilesForm(request.POST)
            if social_form.is_valid():
                artist.twitter_url = social_form.cleaned_data["twitter_url"] or ""
                artist.twitter_show = social_form.cleaned_data["twitter_active"]
                artist.instagram_url = social_form.cleaned_data["instagram_url"] or ""
                artist.instagram_show = social_form.cleaned_data["instagram_active"]
                artist.facebook_url = social_form.cleaned_data["facebook_url"] or ""
                artist.facebook_show = social_form.cleaned_data["facebook_active"]
                artist.save()
                return redirect("about")

    return render(
        request,
        "about.html",
        {
            "artist": artist,
            "bio_form": bio_form,
            "photo_form": photo_form,
            "social_form": social_form,
            "social_profiles": social_profiles,
        },
    )


# ---------------------------------------------------------------------------
# Static-ish helpers
# ---------------------------------------------------------------------------
def how_to_use(request):
    return render(request, "how_to_use.html")
