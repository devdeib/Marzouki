from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from . import views
from TheApp.views import *

app_name = 'dashboard'
urlpatterns = [
    path('admin_home/', views.home, name='admin_home'),
    path('store_items/', views.store_items_list, name='store_items_list'),
    path('add/', views.add_store_item, name='add_store_item'),
    path('store_items/<int:pk>/', views.store_item_detail,
         name='store_item_detail'),
    path('items_bulk_action/', views.items_bulk_action, name='items_bulk_action'),
    path('sections/', views.section_list, name='section_list'),
    path('sections/<int:pk>/', views.section_detail, name='section_detail'),
    path('dash_search/', views.dash_search, name='dash_search'),
    path('section_list/', views.section_list, name='section_list'),
    path('section_detail/<int:section_id>/', views.edit_section, name='section_detail'),
    path('add_section/', views.add_section, name="add_section"),
    path('discounts/', views.discount_list, name="discount_list"),
    path('variation_list/', views.variation_list, name="variation_list"),
    path('edit_section/<int:section_id>/',
         views.edit_section, name="edit_section"),
    path('sections/delete/<int:section_id>/',
         views.delete_section, name='delete_section'),
    path('discounts/', views.discount_list, name='discount_list'),
    path('discount_detail/<int:pk>/', views.discount_detail, name='discount_detail'),
    path('discounts/add/', views.add_discount, name='add_discount'),
    path('discounts/delete/<int:pk>/',
         views.delete_discount, name='delete_discount'),
    path('orders/', views.order_list, name='order_list'),
    path('variations/', views.variation_list, name='variation_list'),
    path('add-variation/', views.add_variation, name='add_variation'),
    path('add-variation-with-choices/', views.add_variation_with_choices,
         name='add_variation_with_choices'),
    path('add-choice-field/', views.add_choice_field,
         name='add_choice_field'),  # Add this line
    path('store_items/<int:pk>/edit/',
         views.edit_store_item, name='edit_store_item'),
    path('delete-choice/<int:choice_id>/',
         views.delete_choice, name='delete_choice'),
    path('delete-variation/<int:variation_id>/',
         views.delete_variation, name='delete_variation'),

    
]
