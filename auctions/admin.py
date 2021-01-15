from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, Listing, Bid, Comment, Watchlist

# Register your models here.

class WatchlistAdmin(admin.ModelAdmin):
    filter_horizontal = ('listing',)

admin.site.register(User, UserAdmin)
admin.site.register(Listing)
admin.site.register(Bid)
admin.site.register(Comment)
admin.site.register(Watchlist, WatchlistAdmin)