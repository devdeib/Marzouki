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

# Create your views here.


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
            return redirect('home')
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
    return render(request, 'home.html')


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
    return render(request, 'paints.html', {'items': items, 'sections': sections, 'itemss': itemss})


def about(request):
    artist = ArtistProfile.get_solo()
    bio_form = ArtistBioForm(instance=artist)
    photo_form = ArtistPhotoForm(instance=artist)

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

    return render(request, 'about.html', {
        'artist': artist,
        'bio_form': bio_form,
        'photo_form': photo_form,
    })

# Optional: Restrict to superusers if you add separate edit views


def superuser_required(user):
    return user.is_superuser


def paint_detail(request, item_id):
    store_item = get_object_or_404(StoreItems, pk=item_id)
    tags_of_item = store_item.tags.all()
    related_items = StoreItems.objects.filter(
        tags__in=tags_of_item).exclude(id=store_item.id).distinct()
    item_variations = ItemVariation.objects.filter(item=store_item)
    variations_and_percentage = store_item.variations.through.objects.filter(
        item=store_item).select_related('variation').all()
    item_images = StoreItemImage.objects.filter(item=store_item)

    variations_with_choices = []
    for item_variation in item_variations:
        choices = Choices.objects.filter(variation=item_variation)
        variations_with_choices.append({
            'variation': item_variation.variation,
            'choices': choices,
        })

    cart_product_form = CartAddProductForm(item=store_item)

    context = {
        'item': store_item,
        'variations_with_choices': variations_with_choices,
        'variation_percentage_info': [
            {'variation_id': vp.variation.id, 'variation_name': vp.variation.name}
            for vp in variations_and_percentage
        ],
        'cart_product_form': cart_product_form,
        'related_items': related_items,
        'item_images': item_images,
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
    return render(request, 'category_page.html', {'section': section, 'items': items, 'sections': sections})


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
    query = request.GET.get('query', '')  # Get the query from GET request
    sections = Section.objects.all()
    if query:
        # Q objects are used to make complex queries with | (OR) and & (AND)
        results = StoreItems.objects.filter(
            Q(item_name__icontains=query) |
            Q(primary_color__name__icontains=query) |
            Q(secondary_color__name__icontains=query) |
            Q(tags__name__icontains=query)
        ).distinct()
    else:
        results = StoreItems.objects.none()

    return render(request, 'search_results.html', {'results': results, 'sections': sections, 'query': query})


def admin(request):
    return render(request, 'base_admin.html')
