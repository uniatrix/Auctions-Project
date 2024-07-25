from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from .models import *
from .forms import CommentForm

def index(request):
    active_listings = Listing.objects.filter(is_active=True)
    
    # Add current bid to each listing
    for listing in active_listings:
        last_bid = Bid.objects.filter(item=listing).last()
        listing.current_bid = last_bid.price if last_bid else listing.starting_bid

    context = {
        "active_listings": active_listings
    }
    return render(request, "auctions/index.html", context)

def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")

def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))

def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")

@login_required
def create_listing(request):
    if request.method == "POST":
        title_html = request.POST["title"]
        description_html = request.POST["description"]
        starting_bid_html = request.POST["starting_bid"]
        image_url_html = request.POST["image_url"]
        category_html = request.POST["category"]
        current_user = request.user

        # Use objects.create() to create and save the listing in one step
        item = Listing.objects.create(
            title=title_html,
            description=description_html,
            starting_bid=starting_bid_html,
            image_url=image_url_html,
            category=category_html,
            is_active=True,
            owner=current_user,
        )
        Bid.objects.create(
            person=current_user,
            item=item,
            price=starting_bid_html
        )

        # Redirect to the index page after creating the listing
        return redirect('index')
    else:
        return render(request, "auctions/create_listing.html")

def listing_detail(request, title):
    listing = get_object_or_404(Listing, title=title)
    bid_list = Bid.objects.filter(item=listing)
    last_bid = bid_list.last()
    current_bid = last_bid.price if last_bid else listing.starting_bid
    is_owner = listing.owner == request.user
    user_won = False
    user_is_highest_bidder = False
    user_watchlist = None

    if not listing.is_active and last_bid and last_bid.person == request.user:
        user_won = True

    if listing.is_active and last_bid and last_bid.person == request.user:
        user_is_highest_bidder = True

    comments = Comment.objects.filter(listing=listing).order_by('-created_at')

    if request.user.is_authenticated:
        user_watchlist = Watchlist.objects.filter(item=listing, person=request.user).exists()

    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.listing = listing
            comment.user = request.user
            comment.save()
            messages.success(request, "Your comment has been added.")
            return redirect('listing_detail', title=listing.title)
    else:
        form = CommentForm()

    context = {
        "current_listing": listing,
        "current_bid": current_bid,
        "is_owner": is_owner,
        "user_won": user_won,
        "user_is_highest_bidder": user_is_highest_bidder,
        "comments": comments,
        "form": form,
        "user_watchlist": user_watchlist
    }
    return render(request, "auctions/listing_detail.html", context)

@login_required
def add_to_watchlist(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)
    watchlist_item = Watchlist.objects.filter(item=listing, person=request.user)
    if watchlist_item.exists():
        watchlist_item.delete()
    else:
        Watchlist.objects.create(item=listing, person=request.user)
    return redirect('listing_detail', title=listing.title)


@login_required
def view_watchlist(request):
    user_watchlist = Watchlist.objects.filter(person=request.user)
    context = {
        "watchlist": user_watchlist
    }
    return render(request, "auctions/view_watchlist.html", context)

from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Listing, Bid

@login_required
def place_bid(request, listing_id):
    user_bid = float(request.POST["user_bid"])
    listing = get_object_or_404(Listing, id=listing_id)
    bid_list = Bid.objects.filter(item=listing)
    last_bid = bid_list.last()
    
    # Determine the current bid to compare against
    current_bid = last_bid.price if last_bid else listing.starting_bid

    if user_bid > current_bid:
        current_user = request.user
        Bid.objects.create(
            person=current_user,
            item=listing,
            price=user_bid
        )
        messages.success(request, "Your bid was placed successfully!")
    else:
        messages.error(request, f"Your bid must be higher than the current bid of ${current_bid}.")
    
    return redirect('listing_detail', title=listing.title)

@login_required
def close_auction(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)

    # Check if the current user is the owner of the listing
    if listing.owner != request.user:
        messages.error(request, "You are not authorized to close this auction.")
        return redirect('index')

    # Close the auction
    listing.is_active = False
    listing.save()

    # Determine the highest bidder
    highest_bid = Bid.objects.filter(item=listing).order_by('-price').first()
    if highest_bid:
        # Notify the highest bidder or handle the winning logic here
        messages.success(request, f"The auction has been closed. The highest bidder is {highest_bid.person.username}.")
    else:
        messages.info(request, "The auction has been closed. No bids were placed.")

    return redirect('index')

def closed(request):
    closed_listings = Listing.objects.filter(is_active=False)
    
    # Add current bid to each listing
    for listing in closed_listings:
        last_bid = Bid.objects.filter(item=listing).last()
        listing.current_bid = last_bid.price if last_bid else listing.starting_bid

    context = {
        "closed_listings": closed_listings
    }
    return render(request, "auctions/closed.html", context)

def categories(request):
    categories = Listing.objects.values_list('category', flat=True).distinct()
    context = {
        'categories': categories
    }
    return render(request, 'auctions/categories.html', context)

def category_listings(request, category):
    listings = Listing.objects.filter(category=category, is_active=True)
    context = {
        'listings': listings,
        'category': category
    }
    return render(request, 'auctions/category_listings.html', context)