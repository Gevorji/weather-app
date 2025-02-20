from django.shortcuts import render
from django.contrib.auth.views import LoginView, LogoutView
from weatherapp.users.forms import UserCreationForm, AuthenticationForm
from django.http import HttpResponse, HttpResponseRedirect


def register_user(request):
    context = {'messages': {}, 'form': UserCreationForm()}
    tmplt_path = 'users/register.html'
    if request.method == 'GET':
        if request.user.is_authenticated:
            return HttpResponseRedirect('/')
        return render(request, tmplt_path, context)
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.full_clean()
            form.save()
            return HttpResponse(f'Yo\'ve been successfuly registered, {form.instance.username}!')
        else:
            context['form'] = form
            return render(request, tmplt_path, context)


class LoginUser(LoginView):
    template_name = 'users/login.html'
    authentication_form = AuthenticationForm
    next_page = '/'


class LogoutUser(LogoutView):
    next_page = '/'
