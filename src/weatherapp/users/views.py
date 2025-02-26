import logging

from django.shortcuts import render
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import login
from weatherapp.users.forms import UserCreationForm, AuthenticationForm
from django.urls import reverse
from django.http import HttpResponseRedirect
logger = logging.getLogger(__name__)


def register_user(request):
    context = {'messages': {}, 'form': UserCreationForm()}
    tmplt_path = 'users/register.html'
    if request.method == 'GET':
        if request.user.is_authenticated:
            return HttpResponseRedirect(reverse('index'))
        return render(request, tmplt_path, context)
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.full_clean()
            form.save()
            return HttpResponse(f'Yo\'ve been successfuly registered, {form.instance.username}!')
            logger.info('Registered user %s', form.instance.username)
            login(request, form.instance)
            return HttpResponseRedirect(reverse('index'))
        else:
            context['form'] = form
            username = request.POST.get('username')
            logger.info('Unsuccessful registration for user %s', username)
            logger.debug('Errors on registration for user %s: %s', username, form.errors)
            return render(request, tmplt_path, context)


class LoginUser(LoginView):
    template_name = 'users/login.html'
    authentication_form = AuthenticationForm
    next_page = '/'

    def form_valid(self, form):
        logger.info('Logged in user %s', form.cleaned_data['username'])
        return super().form_valid(form)

    def form_invalid(self, form):
        logger.info('Unsuccessful login attempt for user %s', form.data.get('username'))
        logger.debug('Errors on login attempt for user %s: %s', form.data.get('username'), form.errors)
        return super().form_invalid(form)

class LogoutUser(LogoutView):
    next_page = '/'

    def post(self, request, *args, **kwargs):
        logger.info('Logged out user %s', request.user.username)
        return super().post(request, *args, **kwargs)
