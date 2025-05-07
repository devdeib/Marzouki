from TheApp.models import StoreItems, ItemVariation, Choices, StoreItemImage, StoreItemVideo
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login
from .forms import *
from .models import *
from cart.forms import CartAddProductForm
from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from dashboard.forms import NewsletterForm
import os
from django.conf import settings


def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            # Check if a user with the same email already exists
            email = form.cleaned_data['email']
            if User.objects.filter(email=email).exists():
                user_exists = True
                return render(request, 'signup.html', {'form': form, 'user_exists': user_exists})

            # Create a new user
            user = form.save()
            user.refresh_from_db()
            user.save()
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=user.username, password=raw_password)
            return redirect('login')
    else:
        form = SignupForm()
    return render(request, 'signup.html', {'form': form})


def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('paints')
        else:
            return redirect('login')
    return render(request, 'login.html')


def home(request):
    
    subscription_form = NewsletterSubscriptionForm()
    hero_image_url = '/media/hero/hero.jpg'

    if request.method == 'POST':
        # Handle image upload from admin
        if request.FILES.get('image') and request.user.is_authenticated and request.user.is_staff:
            uploaded_image = request.FILES['image']
            hero_dir = os.path.join(settings.MEDIA_ROOT, 'hero')
            os.makedirs(hero_dir, exist_ok=True)
            with open(os.path.join(hero_dir, 'hero.jpg'), 'wb+') as f:
                for chunk in uploaded_image.chunks():
                    f.write(chunk)
            return redirect('home')  # refresh with new image

        # Handle newsletter subscription
        elif request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            form = NewsletterSubscriptionForm(request.POST)
            if form.is_valid():
                email = form.cleaned_data['email']
                subscriber, created = NewsletterSubscriber.objects.get_or_create(
                    email=email)
                if not created and not subscriber.is_active:
                    subscriber.is_active = True
                    subscriber.save()
                return JsonResponse({'success': True, 'message': 'Thank you for subscribing!'})
            else:
                errors = form.errors.as_data()
                error_message = "There was an issue with your subscription:"
                if 'email' in errors:
                    for error in errors['email']:
                        if "already exists" in str(error):
                            error_message = "This email is already subscribed."
                        elif "valid email" in str(error):
                            error_message = "Please enter a valid email address."
                        else:
                            error_message = f"Email error: {str(error)}"
                return JsonResponse({'success': False, 'message': error_message}, status=400)

    return render(request, 'home', {
        'subscription_form': subscription_form,
        'hero_image_url': hero_image_url
    })


def paints(request):
    items = StoreItems.objects.all()
    paginator = Paginator(items, 12)
    sections = Section.objects.all()
    page = request.GET.get('page')
    try:
        itemss = paginator.page(page)
    except PageNotAnInteger:
        itemss = paginator.page(1)
    except EmptyPage:
        itemss = paginator.page(paginator.num_pages)
    return render(request, 'paints.html', {'items': items, 'sections': sections, 'itemss': itemss, 'on_paints_page': True, })


def about(request):
    artist = ArtistProfile.get_solo()
    bio_form = ArtistBioForm(instance=artist)
    photo_form = ArtistPhotoForm(instance=artist)

    # Use artist's social profile data directly
    social_profiles = {
        'twitter': {'url': artist.twitter_url, 'show': artist.twitter_show},
        'instagram': {'url': artist.instagram_url, 'show': artist.instagram_show},
        'facebook': {'url': artist.facebook_url, 'show': artist.facebook_show},
    }
    social_form = SocialProfilesForm(initial={
        'twitter_url': artist.twitter_url,
        'twitter_active': artist.twitter_show,
        'instagram_url': artist.instagram_url,
        'instagram_active': artist.instagram_show,
        'facebook_url': artist.facebook_url,
        'facebook_active': artist.facebook_show,
    })

    if request.method == 'POST':
        if 'bio_submit' in request.POST and request.user.is_superuser:
            bio_form = ArtistBioForm(request.POST, instance=artist)
            if bio_form.is_valid():
                bio_form.save()
                return redirect('about')
        elif 'photo_submit' in request.POST and request.user.is_superuser:
            photo_form = ArtistPhotoForm(
                request.POST, request.FILES, instance=artist)
            if photo_form.is_valid():
                photo_form.save()
                return redirect('about')
        elif 'social_submit' in request.POST and request.user.is_superuser:
            social_form = SocialProfilesForm(request.POST)
            if social_form.is_valid():
                # Save social profiles to the artist instance
                artist.twitter_url = social_form.cleaned_data['twitter_url'] or ''
                artist.twitter_show = social_form.cleaned_data['twitter_active']
                artist.instagram_url = social_form.cleaned_data['instagram_url'] or ''
                artist.instagram_show = social_form.cleaned_data['instagram_active']
                artist.facebook_url = social_form.cleaned_data['facebook_url'] or ''
                artist.facebook_show = social_form.cleaned_data['facebook_active']
                artist.save()
                return redirect('about')

    return render(request, 'about.html', {
        'artist': artist,
        'bio_form': bio_form,
        'photo_form': photo_form,
        'social_form': social_form,
        'social_profiles': social_profiles,
    })
# Optional: Restrict to superusers if you add separate edit views


def superuser_required(user):
    return user.is_superuser


def paint_detail(request, item_id):
    store_item = get_object_or_404(StoreItems, pk=item_id)

    # Related tags and items
    tags_of_item = store_item.tags.all()
    related_items = StoreItems.objects.filter(
        tags__in=tags_of_item
    ).exclude(id=store_item.id).distinct()

    # Fetch images and videos
    item_images = StoreItemImage.objects.filter(item=store_item)
    item_videos = StoreItemVideo.objects.filter(item=store_item)

    # Fetch item variations and their corresponding choices
    item_variations = ItemVariation.objects.filter(
        item=store_item).select_related('variation')

    # Structure variations with all related choices
    variations_with_choices = []


    for item_variation in item_variations:
        choices = Choices.objects.filter(variation=item_variation)
        variations_with_choices.append({
            # still pass the base variation object for display
            'variation': item_variation.variation,
            'choices': choices,
        })


    # Initialize cart form with dynamic quantity range
    cart_product_form = CartAddProductForm(item=store_item)

    # Optional: if using percentage discount metadata in future
    variation_percentage_info = [
        {
            'variation_id': item_variation.variation.id,
            'variation_name': item_variation.variation.name
        }
        for item_variation in item_variations
    ]

    context = {
        'item': store_item,
        'variations_with_choices': variations_with_choices,
        'variation_percentage_info': variation_percentage_info,
        'cart_product_form': cart_product_form,
        'related_items': related_items,
        'item_images': item_images,
        'item_videos': item_videos,
    }

    return render(request, 'paint_detail.html', context)


# Make sure the argument here is 'section_id'
def category_browse(request, section_id):
    # Get the specific section
    sections = Section.objects.all()
    section = get_object_or_404(Section, id=section_id)

    # Filter items using the related name 'section'
    items = section.items.all()  # Use the related name 'section' to access related items

    # Render the filtered items to a template
    return render(request, 'category_page.html', {'section': section, 'items': items, 'sections': sections, 'on_paints_page': True, })


def add_to_cart(request, item_id):
    item = get_object_or_404(StoreItems, pk=item_id)
    user = request.user
    # Get the chosen size from the form
    variation = request.POST.get('variation')
    # Get the personalization text from the form
    personalization = request.POST.get('personalization')
    if user.is_authenticated:
        if Cart.objects.filter(user=user, item=item).exists():
            cart_item = Cart.objects.get(user=user, item=item)
            cart_item.save()
        else:
            Cart.objects.create(user=user, item=item, quantity=1)
        cart = Cart(request)
        cart.add(item=item, quantity=1, variation=variation,
                 personalization=personalization)
        return redirect(reverse('paint_detail', args=[item_id]))
    else:
        return redirect('login')


def search(request):
    # Get the query and remove extra whitespace
    query = request.GET.get('query', '').strip()
    sections = Section.objects.all()

    if query:
        # Use Q objects to search across multiple fields
        results = StoreItems.objects.filter(
            Q(item_name__icontains=query) |              # Search in item name
            Q(tags__name__icontains=query) |             # Search in tags
            # Search in primary color name
            Q(primary_color__name__icontains=query) |
            # Search in secondary color name
            Q(secondary_color__name__icontains=query)
        ).distinct()  # Ensure no duplicate results

        # Handle case where colors might be null
        results = results.filter(
            Q(primary_color__isnull=False) | Q(secondary_color__isnull=False) |
            Q(item_name__icontains=query) | Q(tags__name__icontains=query)
        ).distinct()
    else:
        results = StoreItems.objects.none()  # Return empty queryset if no query

    context = {
        'results': results,
        'sections': sections,
        'query': query,
        'on_paints_page': True,
    }
    return render(request, 'search_results.html', context)

def admin(request):
    return render(request, 'base_admin.html')
