"""
Dashboard URL configuration.

Every URL in this module is wrapped with ``staff_required`` at the URL
level — this is an immune layer of authorization that does not depend
on individual view authors remembering to add a decorator.
"""

from django.urls import path

from . import views
from .decorators import staff_required

app_name = "dashboard"


def s(view):
    """Shorthand to wrap a view with the staff_required decorator."""
    return staff_required(view)


urlpatterns = [
    path("admin_home/", s(views.home), name="admin_home"),
    path("store_items/", s(views.store_items_list), name="store_items_list"),
    path("add/", s(views.add_store_item), name="add_store_item"),
    path("store_items/<int:pk>/", s(views.store_item_detail), name="store_item_detail"),
    path("items_bulk_action/", s(views.items_bulk_action), name="items_bulk_action"),

    path("sections/", s(views.section_list), name="section_list"),
    path("sections/<int:pk>/view/", s(views.section_detail), name="section_detail_view"),
    path("dash_search/", s(views.dash_search), name="dash_search"),
    path("section_list/", s(views.section_list), name="section_list_alt"),
    # Historical: `dashboard:section_detail` opens the edit page.
    path("section_detail/<int:section_id>/", s(views.edit_section), name="section_detail"),
    path("add_section/", s(views.add_section), name="add_section"),

    path("discounts/", s(views.discount_list), name="discount_list"),
    path("variation_list/", s(views.variation_list), name="variation_list"),
    path("edit_section/<int:section_id>/", s(views.edit_section), name="edit_section"),
    path("sections/delete/<int:section_id>/", s(views.delete_section), name="delete_section"),

    path("discount_detail/<int:pk>/", s(views.discount_detail), name="discount_detail"),
    path("discounts/add/", s(views.add_discount), name="add_discount"),
    path("discounts/delete/<int:pk>/", s(views.delete_discount), name="delete_discount"),

    path("orders/", s(views.order_list), name="order_list"),

    path("variations/", s(views.variation_list), name="variation_list_alt"),
    path("add-variation/", s(views.add_variation), name="add_variation"),
    path("add-variation-with-choices/", s(views.add_variation_with_choices), name="add_variation_with_choices"),
    path("add-choice-field/", s(views.add_choice_field), name="add_choice_field"),

    path("store_items/<int:pk>/edit/", s(views.edit_store_item), name="edit_store_item"),
    path("delete-choice/<int:choice_id>/", s(views.delete_choice), name="delete_choice"),
    path("delete-variation/<int:variation_id>/", s(views.delete_variation), name="delete_variation"),

    path("users/", s(views.users_list), name="users_list"),
    path("add_tag/", s(views.add_tag), name="add_tag"),
    path("add_section_ajax/", s(views.add_section_ajax), name="add_section_ajax"),

    path("newsletter_list/", s(views.newsletter_list), name="newsletter_list"),
    path("send_newsletter/", s(views.send_newsletter), name="send_newsletter"),

    path("update-items-order/", s(views.update_items_order), name="update_items_order"),
]
