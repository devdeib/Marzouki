from django.urls import path, re_path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login, name='login'),
    path('home/', views.home, name='home'),
    path('paints/', views.paints, name='paints'),
    path('about/', views.about, name='about'),
    path('paints/<int:item_id>/', views.paint_detail, name='paint_detail'),
    path('add_to_cart/<int:item_id>/', views.add_to_cart, name='add_to_cart'),
    path('category/<int:section_id>/', views.category_browse, name='category_browse'),
    path('search/', views.search, name='search'),
]   