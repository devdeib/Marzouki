from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("home/", views.home, name="home_alt"),
    path("signup/", views.signup, name="signup"),
    path("login/", views.login, name="login"),
    path("logout/", views.user_logout, name="logout"),
    path("account/", views.account, name="account"),
    path("paints/", views.paints, name="paints"),
    path("about/", views.about, name="about"),
    path("paints/<int:item_id>/", views.paint_detail, name="paint_detail"),
    path("category/<int:section_id>/", views.category_browse, name="category_browse"),
    path("search/", views.search, name="search"),
    path("originals/", views.originals, name="originals"),
    path("prints/", views.prints, name="prints"),
    path("how-to-use-this-shop/", views.how_to_use, name="how_to_use"),
    path("error/", views.error_500, name="error"),
]

handler500 = "TheApp.views.error_500"
