from django.contrib import admin

from .models import Location, UserLocation

class UserLocationInline(admin.TabularInline):
    list_display = ['user', 'date_added']
    model = UserLocation

class LocationAdmin(admin.ModelAdmin):
    list_display = ['name', 'latitude', 'longitude', 'country']
    inlines = [UserLocationInline]

class UserLocationAdmin(admin.ModelAdmin):
    list_display = ['user', 'location', 'date_added']

admin.site.register(Location, LocationAdmin)
admin.site.register(UserLocation, UserLocationAdmin)
