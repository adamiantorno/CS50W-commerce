from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.db.models import Max

from .models import Listing, Comment, Bid, Watchlist

class ListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        exclude = [
            'creator',
            'date_created',
            'is_active',
            'winner'
        ]
        labels = {
            'title': _(''),
            'description': _(''),
            'image': _(''),
            'start_bid': _('Starting Bid ($)')
        }

    # Initialize placeholders and classes for fields
    def __init__(self, *args, **kwargs):
        super(ListingForm, self).__init__(*args, **kwargs)   
        self.fields['title'].widget.attrs.update(placeholder='Title')
        self.fields['description'].widget.attrs.update(placeholder='Add Description')
        self.fields['start_bid'].widget.attrs.update(placeholder='0.00')
        self.fields['image'].widget.attrs.update(placeholder='Enter Image URL')
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'  
            
class CategoryForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = [
            'category'
        ]

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields  = ['comment']
        labels = {
            'comment': _('')
        }

    def __init__(self, *args, **kwargs):
        super(CommentForm, self).__init__(*args, **kwargs)
        self.fields['comment'].widget.attrs['class'] = 'form-control'        
        self.fields['comment'].widget.attrs['placeholder'] = 'Add a Comment'

class BidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ['bid']
        labels = {
            'bid': _('')
        }
    
    def __init__(self, *args, **kwargs):
        self.listing_id = kwargs.pop('listing_id')
        super(BidForm, self).__init__(*args, **kwargs)
        self.fields['bid'].widget.attrs['class'] = 'form-control'         
        self.fields['bid'].widget.attrs['placeholder'] = '$0.00 - Place a bid'
        

    # Form Validation that bid is greater than starting and highest bid
    def clean_bid(self):
        new_bid = self.cleaned_data['bid']
        og_bid = Listing.objects.get(pk=self.listing_id).start_bid
        highest_bid = og_bid
        if Bid.objects.filter(listing_id=self.listing_id).exists():
            highest_bid = Bid.objects.filter(listing_id=self.listing_id).aggregate(var=Max('bid')).get('var', None) 
        if not (new_bid > highest_bid and new_bid > og_bid):
            self.add_error(None, ValidationError('Error: Your bid must be greater than the current highest bid and starting bid!'))
        return new_bid
    




