from TheApp.models import *
from django.forms import formset_factory
from django.shortcuts import render, get_object_or_404
from django.contrib.admin import site
from django.shortcuts import render, get_object_or_404, redirect
from TheApp.models import *
from django.db.models import Q
from django.shortcuts import render
from django.shortcuts import render
from django.contrib import admin
from django.apps import apps
from django.urls import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from TheApp.models import StoreItems
from .forms import *
from django.contrib import messages
from django.db.models import Count



def home(request):
    app_config = apps.get_app_config('TheApp')

    return render(request, 'admin_home.html')


def store_items_list(request):
    items = StoreItems.objects.all()
    paginator = Paginator(items, 12)  # Show 12 items per page
    sections = Section.objects.all()

    page = request.GET.get('page')  # Get the page number from the request
    try:
        itemss = paginator.page(page)  # Get the items for the requested page
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        itemss = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        itemss = paginator.page(paginator.num_pages)

    return render(request, 'store_items_list.html', {'items': items, 'sections': sections, 'itemss': itemss})


def dash_search(request):
    items = StoreItems.objects.all()
    query = request.GET.get('query', '')  # Get the query from GET request
    paginator = Paginator(items, 12)
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
    
    page = request.GET.get('page')  # Get the page number from the request
    try:
        results = paginator.page(page)  # Get the items for the requested page
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        results = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        results = paginator.page(paginator.num_pages)

    return render(request, 'dash_search_results.html', {'results': results, 'sections': sections, 'query': query})



def add_store_item(request):
    # Assuming a maximum of 3 extra images
    if request.method == 'POST':
        form = StoreItemForm(request.POST, request.FILES)
        if form.is_valid():
            
            form.save()
            
            messages.success(request, 'New listing added successfully!')
            # No redirect; fall through to re-render the form page
        else:
            print("Form is not valid")
    else:
        print("GET request, not POST")
        form = StoreItemForm()
    return render(request, 'add_store_item.html', {'form': form})


def store_item_detail(request, pk):
    store_item = get_object_or_404(StoreItems, pk=pk)
    return render(request, 'store_item_detail.html', {'store_item': store_item})


def section_list(request):
    sections = Section.objects.annotate(item_count=Count('items'))
    return render(request, 'section_list.html', {'sections': sections})


def add_section(request):
    # Assuming a maximum of 3 extra images
    if request.method == 'POST':
        form = SectionForm(request.POST, request.FILES)
        if form.is_valid():

            form.save()

            messages.success(request, 'New Category added successfully!')
            # No redirect; fall through to re-render the form page
        else:
            print("Form is not valid")
    else:
        print("GET request, not POST")
        form = SectionForm()
    return render(request, 'add_section.html', {'form': form})


def edit_section(request, section_id):
    section = Section.objects.get(id=section_id)
    items = StoreItems.objects.all()

    if request.method == 'POST':
        print("POST request received.")
        print("POST data:", request.POST)

        form = SectionForm(request.POST, instance=section)
        if form.is_valid():
            print("Form is valid.")
            # Save the form instance
            section = form.save(commit=False)
            # Process selected items
            selected_items = form.cleaned_data['items']
            section.items.set(selected_items)
            section.save()
            return redirect('dashboard:section_list')
        else:
            print("Form errors:", form.errors)
    else:
        form = SectionForm(instance=section)

    # Separate checked and unchecked items
    checked_items = []
    unchecked_items = []

    for item in items:
        if item in section.items.all():
            checked_items.append(item)
        else:
            unchecked_items.append(item)

    sorted_items = checked_items + unchecked_items

    return render(request, 'section_detail.html', {'form': form, 'section': section, 'items': sorted_items})


def delete_section(request, section_id):
    section = get_object_or_404(Section, id=section_id)
    section.delete()
    return redirect('dashboard:section_list')

def section_detail(request, pk):
    section = get_object_or_404(Section, pk=pk)
    return render(request, 'section_detail.html', {'section': section})


def color_list(request):
    colors = Color.objects.all()
    return render(request, 'color_list.html', {'colors': colors})


def color_detail(request, pk):
    color = get_object_or_404(Color, pk=pk)
    return render(request, 'color_detail.html', {'color': color})


def tag_list(request):
    tags = Tag.objects.all()
    return render(request, 'tag_list.html', {'tags': tags})


def tag_detail(request, pk):
    tag = get_object_or_404(Tag, pk=pk)
    return render(request, 'tag_detail.html', {'tag': tag})


def discount_list(request):
    discounts = Discount.objects.all()
    return render(request, 'discounts.html', {'discounts': discounts})


def discount_detail(request, pk):
    discount = get_object_or_404(Discount, pk=pk)
    return render(request, 'dashboard/discount_detail.html', {'discount': discount})


def variation_list(request):
    variations = Variation.objects.all()
    return render(request, 'variation_list.html', {'variations': variations})


def variation_detail(request, pk):
    variation = get_object_or_404(Variation, pk=pk)
    return render(request, 'variation_detail.html', {'variation': variation})


def item_variation_list(request):
    item_variations = ItemVariation.objects.all()
    return render(request, 'item_variation_list.html', {'item_variations': item_variations})


def item_variation_detail(request, pk):
    item_variation = get_object_or_404(ItemVariation, pk=pk)
    return render(request, 'item_variation_detail.html', {'item_variation': item_variation})


def model_list(request, model_name):
    model_admin = site._registry.get(model_name)
    if model_admin:
        model_queryset = model_admin.model.objects.all()
        return render(request, f'dashboard/{model_name}_list.html', {'objects': model_queryset})
    else:
        return render(request, 'dashboard/model_not_found.html', {'model_name': model_name})


def model_detail(request, model_name, pk):
    model_admin = site._registry.get(model_name)
    if model_admin:
        model_instance = get_object_or_404(model_admin.model, pk=pk)
        return render(request, f'dashboard/{model_name}_detail.html', {'object': model_instance})
    else:
        return render(request, 'dashboard/model_not_found.html', {'model_name': model_name})
