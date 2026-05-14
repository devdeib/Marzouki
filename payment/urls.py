from django.urls import path

from . import views, webhooks

app_name = "payment"

urlpatterns = [
    path("process/", views.payment_process, name="process"),
    path("completed/", views.payment_completed, name="completed"),
    path("canceled/", views.payment_canceled, name="canceled"),
    # NOTE: also mounted at /stripe/webhook/ from the project urls.py so the
    # public-facing path is short and stable for the Stripe dashboard.
    path("webhook/", webhooks.stripe_webhook, name="webhook"),
]
