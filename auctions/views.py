from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db import IntegrityError
from django.db.models import Max
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import View, CreateView, ListView, DetailView, FormView
from django.views.generic.edit import FormMixin, SingleObjectMixin

from .models import User, Listing, Bid, Comment, Watchlist
from .forms import ListingForm, CategoryForm, CommentForm, BidForm


# List all Active listings
class ListingListView(ListView):
    form_class = CategoryForm
    template_name = 'auctions/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CategoryForm()
        return context

    #  Get specific categories and order by most recently created
    def get_queryset(self):
        queryset = Listing.objects.filter(is_active=True).order_by('-date_created')
        if self.request.GET.get('category'):
            if self.request.GET.get('category') is not None:
                queryset = Listing.objects.filter(category=self.request.GET.get('category')).order_by('-date_created')
        return queryset


# List all Listing on logged in users watchlist
@method_decorator(login_required, name='dispatch')
class WatchlistListView(ListView):
    template_name = 'auctions/watchlist.html'
   
    def get_queryset(self):
        queryset = Listing.objects.filter(watchlists__user=self.request.user)
        return queryset


# Add or remove listing to watchlist
@login_required
def watch_update(request, product_id):
    # Get objects to edit
    listing = Listing.objects.get(id=product_id)
    if Watchlist.objects.filter(user=request.user).exists():
        watch = Watchlist.objects.get(user=request.user)
    else:
        watch = Watchlist.objects.create(user=request.user)
    
    #Add or remove from watchlist
    if listing.watchlists.filter(user=request.user).exists():
        watch.listing.remove(listing)
    else:
        watch.listing.add(listing)
    watch.save()
    return HttpResponseRedirect(reverse('listing', kwargs={'pk': product_id}))


# Close bid and determine winner
def close_bid(request, product_id):
    # Get objects and variables
    listing = Listing.objects.get(id=product_id)
    highest_bid = Bid.objects.filter(listing_id=product_id).order_by('-bid')[0]
    # Set listing values
    listing.winner = highest_bid.user
    listing.is_active = False
    listing.save()
    return HttpResponseRedirect(reverse('listing', kwargs={'pk': product_id}))


# Listing Detail Page
@method_decorator(login_required, name='post')
class ListingDetailView(FormMixin, DetailView):
    model = Listing
    template_name = 'auctions/listing.html'
    form_class = CommentForm
    second_form_class = BidForm

    # Return to same page if post is successful 
    def get_success_url(self):
        return reverse('listing', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # watchlist context
        if self.request.user.is_authenticated:
            context['on_watchlist'] = Watchlist.objects.filter(listing__id=self.object.pk, user=self.request.user).exists()
        # comment context 
        context['commentform'] = CommentForm()
        context['comments'] = Comment.objects.filter(listing_id=self.object.pk).order_by('-timestamp')
        # bidding context
        if not 'bidform' in kwargs:
            context['bidform'] = BidForm(listing_id=self.object.pk)
        if Bid.objects.filter(listing_id=self.object.pk).exists():
            context['highest_bid'] = Bid.objects.filter(listing_id=self.object.pk).aggregate(var=Max('bid')).get('var', None)
            context['bidder'] = User.objects.get(bids__bid=context['highest_bid'])
            context['num_bids'] = Bid.objects.filter(listing_id=self.object.pk).count()
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        # Comment Form
        if request.POST.get('comment'):
            form = CommentForm(request.POST)
            if form.is_valid():
                return self.comment_form_valid(form)
            else:
                return self.form_invalid(form)
        # Bid Form
        elif request.POST.get('bid'):
            form = BidForm(data=request.POST, listing_id=self.object.pk)
            if form.is_valid():
                return self.bid_form_valid(form)
            else:
                return self.render_to_response(self.get_context_data(bidform=form))
        
    # Set commenter as logged in user
    def comment_form_valid(self, form):
        comment = form.save(commit=False)
        comment.listing = Listing.objects.get(pk=self.object.pk)
        comment.user = User.objects.get(username=self.request.user)
        comment.save()
        return super().form_valid(form)  

    # Set bidder as logged in user
    def bid_form_valid(self, form):
        new_bid = form.save(commit=False)
        new_bid.listing = Listing.objects.get(pk=self.object.pk)
        new_bid.user = User.objects.get(username=self.request.user)
        new_bid.save()
        return super().form_valid(form)  


# Create a new lisitng if logged in 
@method_decorator(login_required, name='dispatch')
class ListingCreateView(CreateView):
    form_class = ListingForm
    template_name = 'auctions/create.html'

    # need to lock into currently logged in user
    def form_valid(self, form):
        listing = form.save(commit=False)
        listing.creator = User.objects.get(username=self.request.user)
        listing.save()
        return HttpResponseRedirect(reverse('index'))


# Login Page
def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


# Logout
def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


# Register new user
def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
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

# # https://github.com/django/django/blob/master/docs/topics/class-based-views/mixins.txt
# class ListingDisplay(DetailView):
#     model = Listing
#     template_name = 'auctions/listing.html'

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['commentform'] = CommentForm()
#         context['comments'] = Comment.objects.filter(listing_id=self.object.pk).order_by('-timestamp')
#         context['bidform'] = BidForm(listing_id=self.object.pk)
#         if Bid.objects.filter(listing_id=self.object.pk).exists():
#             context['highest_bid'] = Bid.objects.filter(listing_id=self.object.pk).aggregate(var=Max('bid')).get('var', None)
#             context['bidder'] = User.objects.get(bids__bid=context['highest_bid'])
#             context['num_bids'] = Bid.objects.filter(listing_id=self.object.pk).count()
#         context['on_watchlist'] = Watchlist.objects.filter(listing__id=self.object.pk, user=self.request.user)
#         return context


# @method_decorator(login_required, name='dispatch')
# class ListingInterest(SingleObjectMixin, FormView):
#     model = Listing
#     template_name = 'auctions/listing.html'
#     form_class = CommentForm
#     second_form_class = BidForm

#     def get_success_url(self):
#         return reverse('listing', kwargs={'pk': self.object.pk})

#     def post(self, request, *args, **kwargs):
#         self.object = self.get_object()
#         if request.POST.get('comment'):
#             # form_class = self.get_form_class()
#             form = CommentForm(request.POST)
#             if form.is_valid():
#                 return self.comment_form_valid(form)
#             else:
#                 return self.form_invalid(form)
#         elif request.POST.get('bid'):
#             # form_class = self.second_form_class
#             form = BidForm(data=request.POST, listing_id=self.object.pk)
#             if form.is_valid():
#                 return self.bid_form_valid(form)
#             else: 
#                 print(form.errors)
#                 return HttpResponseRedirect(self.get_success_url())
        
#     def comment_form_valid(self, form):
#         comment = form.save(commit=False)
#         comment.listing = Listing.objects.get(pk=self.object.pk)
#         comment.user = User.objects.get(username=self.request.user)
#         comment.save()
#         return super().form_valid(form)  

#     def bid_form_valid(self, form):
#         new_bid = form.save(commit=False)
#         new_bid.listing = Listing.objects.get(pk=self.object.pk)
#         new_bid.user = User.objects.get(username=self.request.user)
#         new_bid.save()
#         return super().form_valid(form)  


# # Connext lisitng Detail and Post Items
# class ListingDetailView(View):

#     def get(self, request, *args, **kwargs):
#         view = ListingDisplay.as_view()
#         return view(request, *args, **kwargs)

#     def post(self, request, *args, **kwargs):
#         view = ListingInterest.as_view()
#         return view(request, *args, **kwargs)