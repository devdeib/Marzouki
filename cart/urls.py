from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from . import views
from TheApp.views import *

app_name = "cart"

urlpatterns = [
    path("", views.cart_detail, name="cart_detail"),
    path("add/<int:item_id>/", views.cart_add, name="cart_add"),
    path("remove/<int:item_id>/", views.cart_remove, name="cart_remove"),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
