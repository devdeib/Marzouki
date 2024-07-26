from TheApp.models import *
from django.shortcuts import render, get_object_or_404
from django.contrib.admin import site
from django.shortcuts import render, get_object_or_404, redirect
from TheApp.models import *
from django.shortcuts import render
from django.shortcuts import render
from django.contrib import admin
from django.apps import apps
from django.urls import reverse


def home(request):
    app_config = apps.get_app_config('TheApp')

    return render(request, 'admin_home.html')


def store_items_list(request):
    store_items = StoreItems.objects.all()
    return render(request, 'store_items_list.html', {'store_items': store_items})


def store_item_detail(request, pk):
    store_item = get_object_or_404(StoreItems, pk=pk)
    return render(request, 'store_item_detail.html', {'store_item': store_item})


def section_list(request):
    sections = Section.objects.all()
    return render(request, 'section_list.html', {'sections': sections})


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
    return render(request, 'discount_list.html', {'discounts': discounts})


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
