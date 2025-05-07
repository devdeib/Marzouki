from TheApp.forms import *
from .models import *
from django.forms import modelformset_factory
from django.shortcuts import render, redirect
from django.shortcuts import render, redirect, get_object_or_404
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
from TheApp.models import *
from .forms import *
from dashboard.forms import *
from django.contrib import messages
from django.db.models import Count
from orders.models import Order
import logging
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Min, Max
from django.conf import settings
from django.core.mail import send_mass_mail
from django.core.mail import EmailMultiAlternatives


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

    return render(request, 'store_items_list.html', {'items': items, 'sections': sections, 'itemss': itemss, 'on_dashboard_page': True, })


def items_bulk_action(request):
    if request.method == 'POST':
        action = request.GET.get('action')
        selected_items = request.POST.getlist('items')

        if selected_items:
            items = StoreItems.objects.filter(pk__in=selected_items)
            if action == 'AC':
                items.update(status=StoreItems.ACTIVE)
            elif action == 'DR':
                items.update(status=StoreItems.DRAFT)
            elif action == 'IN':
                items.update(status=StoreItems.INACTIVE)
            elif action == 'delete':
                items.delete()

    return redirect('dashboard:store_items_list')


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

    return render(request, 'dash_search_results.html', {'results': results, 'sections': sections, 'query': query, 'on_dashboard_page': True,})


logger = logging.getLogger(__name__)


def add_store_item(request):
    # Handle AJAX video upload (unchanged)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.method == 'POST':
        try:
            video_file = next(iter(request.FILES.values()))
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    if request.method == 'POST':
        store_item_form = StoreItemForm(request.POST, request.FILES)
        image_formset = StoreItemImageFormSet(
            request.POST, request.FILES, prefix='images')
        video_formset = StoreItemVideoFormSet(
            request.POST, request.FILES, prefix='videos')
        variation_formset = ItemVariationsFormSet(
            request.POST, prefix='variation')

        choices_formsets = []
        total_variations = int(request.POST.get('variation-TOTAL_FORMS', 0))
        for i in range(total_variations):
            choices_formset = ChoiceFormSet(
                request.POST, prefix=f'choices_{i}')
            choices_formsets.append(choices_formset)
        choices_valid = all(formset.is_valid() for formset in choices_formsets)

        if (store_item_form.is_valid() and image_formset.is_valid() and
                video_formset.is_valid() and variation_formset.is_valid() and choices_valid):
            try:
                with transaction.atomic():
                    # Save store item
                    store_item = store_item_form.save()
                    # Link the selected section (if any)
                    selected_section = store_item_form.cleaned_data.get(
                        'section')
                    if selected_section:
                        selected_section.items.add(store_item)

                    # Save images
                    image_formset.instance = store_item
                    image_formset.save()
                    # Save videos
                    video_formset.instance = store_item
                    video_formset.save()
                    # Save variations
                    variations = variation_formset.save(commit=False)
                    for i, variation in enumerate(variations):
                        variation.item = store_item
                        variation.save()
                        choices_formsets[i].instance = variation
                        choices_formsets[i].save()
                    messages.success(
                        request, 'Store item created successfully!')
                    return redirect('dashboard:store_items_list')
            except Exception as e:
                messages.error(request, f'Error saving item: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        store_item_form = StoreItemForm()
        image_formset = StoreItemImageFormSet(prefix='images')
        video_formset = StoreItemVideoFormSet(prefix='videos')
        variation_formset = ItemVariationsFormSet(prefix='variation')
        choices_formsets = [ChoiceFormSet(prefix='choices_0')]

    context = {
        'store_item_form': store_item_form,
        'image_formset': image_formset,
        'video_formset': video_formset,
        'variation_formset': variation_formset,
        'choices_formsets': choices_formsets,
        'is_edit': False,
        'on_dashboard_page': True,
    }
    return render(request, 'add_store_item.html', context)

# New AJAX view to create a section


def newsletter_list(request):
    subscribers = NewsletterSubscriber.objects.all()
    return render(request, 'newsletter_list.html', {'subscribers': subscribers, 'on_dashboard_page':True})


def send_newsletter(request):
    if request.method == 'POST':
        form = NewsletterForm(request.POST)
        if form.is_valid():
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            from_email = 'Paint Store <myartstore@gmail.com>'
            subscribers = NewsletterSubscriber.objects.filter(is_active=True)

            if not subscribers:
                messages.error(request, "No active subscribers found.")
                return redirect('dashboard:newsletter_list')

            for subscriber in subscribers:
                html_content = f"""
                <html>
                    <body>
                        <h2>{subject}</h2>
                        <p>{message}</p>
                        <p><small>To unsubscribe, <a href="#">click here</a>.</small></p>
                    </body>
                </html>
                """
                email = EmailMultiAlternatives(
                    subject, message, from_email, [subscriber.email])
                email.attach_alternative(html_content, "text/html")
                email.send(fail_silently=False)

            messages.success(
                request, f"Newsletter sent to {subscribers.count()} subscribers!")
            return redirect('dashboard:newsletter_list')
        else:
            messages.error(request, "Please correct the form errors.")
    else:
        form = NewsletterForm()
    return render(request, 'send_newsletter.html', {'form': form, 'on_dashboard_page': True})


def add_section_ajax(request):
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            if name:
                section = Section.objects.create(name=name)
                return JsonResponse({
                    'success': True,
                    'section': {
                        'id': section.id,
                        'name': section.name
                    }
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Section name is required'
                })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    })

def add_variation(request):
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            if name:
                variation = Variation.objects.create(name=name)
                return JsonResponse({
                    'success': True,
                    'variation': {
                        'id': variation.id,
                        'name': variation.name
                    }
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Variation name is required'
                })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    })

def edit_store_item(request, pk):
    store_item = get_object_or_404(StoreItems, pk=pk)

    if request.method == 'POST':
        store_item_form = StoreItemForm(
            request.POST, request.FILES, instance=store_item)
        image_formset = StoreItemImageFormSet(request.POST, request.FILES,
                                              instance=store_item, prefix='images')
        video_formset = StoreItemVideoFormSet(request.POST, request.FILES,
                                              instance=store_item, prefix='videos')
        variation_formset = ItemVariationsFormSet(
            request.POST, prefix='variation')

        # Handle choices formsets
        total_variations = int(request.POST.get('variation-TOTAL_FORMS', 0))
        choices_formsets = []
        for i in range(total_variations):
            choices_formset = ChoiceFormSet(
                request.POST,
                prefix=f'choices_{i}'
            )
            choices_formsets.append(choices_formset)

        choices_valid = all(formset.is_valid() for formset in choices_formsets)

        if (store_item_form.is_valid() and image_formset.is_valid() and
            video_formset.is_valid() and variation_formset.is_valid() and
                choices_valid):
            try:
                with transaction.atomic():
                    # Save main form
                    store_item = store_item_form.save()

                    # Save images
                    image_formset.save()

                    # Save videos
                    video_formset.save()

                    # Save variations and choices
                    variations = variation_formset.save(commit=False)
                    for i, variation in enumerate(variations):
                        variation.item = store_item
                        variation.save()
                        choices_formsets[i].instance = variation
                        choices_formsets[i].save()

                    messages.success(
                        request, 'Store item updated successfully!')
                    return redirect('dashboard:store_items_list')
            except Exception as e:
                messages.error(request, f'Error updating item: {str(e)}')
    else:
        store_item_form = StoreItemForm(instance=store_item)
        image_formset = StoreItemImageFormSet(
            instance=store_item, prefix='images')
        video_formset = StoreItemVideoFormSet(
            instance=store_item, prefix='videos')

        # Get existing variations
        variations = store_item.item_variations.all()
        variation_formset = ItemVariationsFormSet(
            instance=store_item,
            prefix='variation',
            queryset=variations
        )

        # Create choices formsets
        choices_formsets = []
        for i, variation in enumerate(variations):
            choices_formset = ChoiceFormSet(
                prefix=f'choices_{i}',
                instance=variation,
            )
            choices_formsets.append(choices_formset)

        if not choices_formsets:
            choices_formsets = [ChoiceFormSet(prefix='choices_0')]

    context = {
        'store_item_form': store_item_form,
        'image_formset': image_formset,
        'video_formset': video_formset,
        'variation_formset': variation_formset,
        'choices_formsets': choices_formsets,
        'store_item': store_item,
        'is_edit': True
    }

    return render(request, 'edit_store_item.html', context)


def delete_choice(request, choice_id):
    """Delete a specific choice."""
    if request.method == 'POST':
        try:
            choice = get_object_or_404(Choices, id=choice_id)
            choice.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def add_tag(request):
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            if name:
                tag, created = Tag.objects.get_or_create(name=name)
                return JsonResponse({
                    'success': True,
                    'tag': {
                        'id': tag.id,
                        'name': tag.name
                    }
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Tag name is required'
                })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    })


def delete_variation(request, variation_id):
    """Delete a variation and all its associated choices."""
    if request.method == 'POST':
        try:
            variation = get_object_or_404(ItemVariation, id=variation_id)
            # This will automatically delete associated choices due to CASCADE
            variation.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def add_variation_with_choices(request):
    form_index = int(request.GET.get('form_index', 0))
    variation_form = ItemVariationsForm(prefix=f'variation-{form_index}')
    choices_formset = ChoiceFormSet(prefix=f'choices_{form_index}')
    context = {
        'form_index': form_index,
        'variation_form': variation_form,
        'choices_formset': choices_formset,
    }
    return render(request, 'variation_with_choices.html', context)

def add_choice_field(request):
    variation_index = request.GET.get('variation_index', 0)
    choice_index = request.GET.get('choice_index', 0)

    # Create a single choice form
    choice_form = ChoiceForm(
        prefix=f'choices_{variation_index}-{choice_index}')

    context = {
        'choice_form': choice_form,
        'variation_index': variation_index,
        'choice_index': choice_index,
    }
    return render(request, 'add_choice_field.html', context)


def store_item_detail(request, pk):
    store_item = get_object_or_404(StoreItems, pk=pk)
    return render(request, 'store_item_detail.html', {'store_item': store_item})


def section_list(request):
    sections = Section.objects.annotate(item_count=Count('items'))
    return render(request, 'section_list.html', {'sections': sections, 'on_dashboard_page': True, })


def add_section(request):
    # Assuming a maximum of 3 extra images
    if request.method == 'POST':
        form = SectionForm(request.POST, request.FILES)
        if form.is_valid():

            form.save()

            messages.success(request, 'New Category added successfully!')
            # No redirect; fall through to re-render the form page
            return redirect('dashboard:section_list')
        else:
            print("Form is not valid")
    else:
        print("GET request, not POST")
        form = SectionForm()
    return render(request, 'add_section.html', {'form': form, 'on_dashboard_page':True})


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

    return render(request, 'section_detail.html', {'form': form, 'section': section, 'items': sorted_items, 'on_dashboard_page': True})


def delete_section(request, section_id):
    section = get_object_or_404(Section, id=section_id)
    section.delete()
    return redirect('dashboard:section_list')


def section_detail(request, pk):
    section = get_object_or_404(Section, pk=pk)
    return render(request, 'section_detail.html', {'section': section, 'on_section_page': True})


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
    return render(request, 'discounts.html', {'discounts': discounts, 'on_dashboard_page': True})


def discount_detail(request, pk):
    discount = get_object_or_404(Discount, pk=pk)

    if request.method == 'POST':
        form = DiscountForm(request.POST, instance=discount)
        if form.is_valid():
            form.save()
            return redirect('dashboard:discount_list')
    else:
        form = DiscountForm(instance=discount)

    return render(request, 'discount_detail.html', {'form': form, 'discount': discount, 'on_dashboard_page': True})


def add_discount(request):
    if request.method == "POST":
        form = DiscountForm(request.POST)
        if form.is_valid():
            discount = form.save()  # Save the discount without updating items
            return redirect('dashboard:discount_list')
    else:
        form = DiscountForm()
    return render(request, 'add_discount.html', {'form': form, 'on_dashboard_page': True})


def delete_discount(request, pk):
    discount = get_object_or_404(Discount, pk=pk)
    discount.delete()
    return redirect('dashboard:discount_list')


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
        model_instance = get_object_or_404(
            model_admin.model.objects.all(), pk=pk)
        return render(request, f'dashboard/{model_name}_detail.html', {'object': model_instance})
    else:
        return render(request, 'dashboard/model_not_found.html', {'model_name': model_name})


def order_list(request):
    orders = Order.objects.all()

    selected_year = request.GET.get('year', '')
    selected_month = request.GET.get('month', '')

    if selected_year:
        try:
            orders = orders.filter(created__year=int(selected_year))
        except ValueError:
            orders = Order.objects.none()  # Invalid year, show no results

    if selected_month:
        try:
            orders = orders.filter(created__month=int(selected_month))
        except ValueError:
            orders = Order.objects.none()  # Invalid month, show no results

    # Get year range safely
    year_range = orders.aggregate(min_year=Min(
        'created__year'), max_year=Max('created__year'))
    min_year = year_range['min_year'] or 2020
    max_year = year_range['max_year'] or 2025
    years = range(min_year, max_year +
                  1) if min_year and max_year else range(2020, 2026)

    context = {
        'orders': orders,
        'years': years,
        'selected_year': selected_year,
        'selected_month': selected_month,
        'on_dashboard_page': True,
    }
    return render(request, 'order_list.html', context)


def variation_list(request):
    variations = Variation.objects.all()
    item_variations = ItemVariation.objects.all()
    return render(request, 'variation_list.html', {'variations': variations, 'item_variations': item_variations})

def users_list(request):
    users = User.objects.all()
    return render(request, 'users_list.html', {'users': users, 'on_dashboard_page': True})