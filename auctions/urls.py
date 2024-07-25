from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("create_listing", views.create_listing, name="create_listing"),
    path("commerce/<str:title>", views.listing_detail, name="listing_detail"),
    path("add_to_watchlist/<int:listing_id>/", views.add_to_watchlist, name="add_to_watchlist"),
    path("view_watchlist", views.view_watchlist, name="view_watchlist"),
    path("place_bid/<int:listing_id>/", views.place_bid, name="place_bid"),
    path('close_auction/<int:listing_id>/', views.close_auction, name='close_auction'),
    path("closed", views.closed, name="closed"),
    path('categories/', views.categories, name='categories'),
    path('category/<str:category>/', views.category_listings, name='category_listings'),
]