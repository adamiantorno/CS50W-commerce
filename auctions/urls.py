from django.urls import path

from . import views

urlpatterns = [
    path("", views.ListingListView.as_view(), name="index"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register, name="register"),
    path("create/", views.ListingCreateView.as_view() , name="create"),
    path("listing/<int:pk>", views.ListingDetailView.as_view(), name="listing"),
    path("watchlist", views.WatchlistListView.as_view(), name="watchlist"),
    path("update/<int:product_id>", views.watch_update, name="watch_update"),
    path("close/<int:product_id>", views.close_bid, name="close_bid")
]
