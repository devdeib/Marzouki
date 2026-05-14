from django.conf import settings
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from payment.webhooks import stripe_webhook

from TheApp import views as app_views
from TheApp.sitemaps import SectionSitemap, StaticViewSitemap, StoreItemSitemap

_SITEMAPS = {
    "static": StaticViewSitemap,
    "sections": SectionSitemap,
    "items": StoreItemSitemap,
}

urlpatterns = [
    path("robots.txt", app_views.robots_txt),
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": _SITEMAPS},
        name="django.contrib.sitemaps.views.sitemap",
    ),
    path("admin/", admin.site.urls),
    path("cart/", include("cart.urls", namespace="cart")),
    path("orders/", include("orders.urls", namespace="orders")),
    path("payment/", include("payment.urls", namespace="payment")),
    path("dashboard/", include(("dashboard.urls", "dashboard"))),
    # Stable, short webhook path for the Stripe dashboard:
    path("stripe/webhook/", stripe_webhook, name="stripe_webhook"),
    path("", include("TheApp.urls")),
    path("", include("django.contrib.auth.urls")),
]

# In DEBUG, serve media via Django.  In production, Nginx serves /media/.
if settings.DEBUG:
    from django.conf.urls.static import static

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
