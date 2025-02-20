from django import forms
from django.utils.translation import gettext_lazy as _


class LocationSearchForm(forms.Form):
    template_name = 'weather/forms/location-search-form.html'
    location_name = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'class': 'form-control me-2', 'placeholder': _('Enter location name'),
                'type': 'search', 'name': 'location'
            }
        )
    )
