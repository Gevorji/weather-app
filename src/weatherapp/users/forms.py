from django.contrib.auth.forms import UserCreationForm as _UserCreationForm, AuthenticationForm as _AuthenticationForm


class UserCreationForm(_UserCreationForm):
    template_name = 'users/forms/users_base_form.html'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})


class AuthenticationForm(_AuthenticationForm):
    template_name = 'users/forms/users_base_form.html'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['password'].widget.attrs.update({'class': 'form-control'})
