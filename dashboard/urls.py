from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from . import views
from TheApp.views import *

app_name = 'dashboard'
urlpatterns = [
    path('admin_home/', views.home, name='admin_home'),
    path('store_items/', views.store_items_list, name='store_items_list'),
    path('store_items/<int:pk>/', views.store_item_detail,
         name='store_item_detail'),
    path('sections/', views.section_list, name='section_list'),
    path('sections/<int:pk>/', views.section_detail, name='section_detail'),
   
]
