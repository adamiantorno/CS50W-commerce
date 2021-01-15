from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from django.db import models

from datetime import date


class User(AbstractUser):
    pass

class Listing(models.Model):
    CATEGORIES = (
        ('ART', 'Art'),
        ('CLT', 'Clothing & Accessories'),
        ('ELE', 'Electronics'),
        ('HME', 'Home'),
        ('KIT', 'Kitchen'),
        ('ENT', 'Entertainment'),
        ('TOY', 'Toys & Games'),
        ('SPT', 'Sports & Outdoors')
    )

    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listings', editable=False)
    title = models.CharField(max_length=100)
    description = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)
    image = models.URLField(max_length=264, blank=True, null=True)
    start_bid = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=50, choices=CATEGORIES)
    is_active = models.BooleanField(default=True)
    winner = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"${self.start_bid} {self.title} - {self.creator}"

    def get_absolute_url(self):
        return reverse('listing', kwargs={'pk': self.pk})


class Bid(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bids')
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='bids')
    bid = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"${self.bid} for {self.listing} from {self.user}"


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='comments')
    comment = models.CharField(max_length=500)
    timestamp = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def __str__(self):
        return f"{self.comment} - {self.user}"


class Watchlist(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    listing = models.ManyToManyField(Listing, blank=True, related_name='watchlists')

    def __str__(self):
        return f"{self.user}'s Watchlist"





