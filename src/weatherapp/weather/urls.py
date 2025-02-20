from django.urls import path
from . import views

app_name = 'weather'

urlpatterns = [
    path('', views.LocationsView.as_view(), name='locations'),
    path('remove/', views.LocationRemoveView.as_view(), name='locations-remove')
]
