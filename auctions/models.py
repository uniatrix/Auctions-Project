from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass

class Listing(models.Model):
    title = models.CharField(max_length=200)
    description = models.CharField(max_length=200)
    starting_bid = models.FloatField()
    image_url = models.CharField(max_length=500, blank=True)
    category = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    owner = models.ForeignKey(User, related_name="listing_owner", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Watchlist(models.Model):
    item = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="watchlist_item")
    person = models.ForeignKey(User, on_delete=models.CASCADE, related_name="watchlist_user")

class Bid(models.Model):
    person = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bidding_user")
    item = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="bidding_item")
    price = models.FloatField()

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="comments")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.listing.title}"