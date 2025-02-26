import contextlib
import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F
from django.forms import model_to_dict
from django.http import HttpResponseRedirect, HttpResponseBadRequest
from django.shortcuts import render, get_object_or_404
from django.views import View
from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator

from weatherapp.weather.models import Location, UserLocation, lati_rounder, longi_rounder
from weatherapp.weather.forms import LocationSearchForm
from weatherapp.external_services import openweathermap
from weatherapp.external_services.openweathermap.errors import OpenweathermapApiHTTPResponseError

SAVE_LOCATIONS_ONLY_WHEN_ADDED_BY_USER = getattr(settings, 'WEATHERAPP_SAVE_LOCATIONS_ONLY_WHEN_ADDED_BY_USER', True)
API_ERROR_MSG = getattr(settings, 'WEATHERAPP_EXTERNAL_API_ERROR_MSG', 'While working on your request, error appeared '
                                                                       'in attempt to interact with external '
                                                                       'web service. Please try again later.')
NLOCATIONS_ON_PAGE = getattr(settings, 'NLOCATIONS_ON_PAGE', 5)


logger = logging.getLogger(__name__)


class IndexView(View):
    location_search_form = LocationSearchForm

    def get(self, request):
        ruser = request.user
        try:
            page_num = int(request.GET.get('page', 1))
        except ValueError:
            page_num = 1
        if not ruser.is_authenticated:
            return render(request, 'weather/guest_index.html')
        users_locations = Location.objects.filter(
            users=ruser
        ).annotate(date_added=F('userlocation__date_added')).order_by('-date_added')
        tmpl_name = 'weather/index.html'
        logger.debug('Fetched %s users (%s) locations', len(users_locations), ruser.username)

        paginator = Paginator(users_locations, NLOCATIONS_ON_PAGE)
        if page_num <= 0:
            page_num = 1
        elif page_num > paginator.num_pages:
            page_num = paginator.num_pages

        locations_page = paginator.page(page_num)
        try:
            locations_weather = [
                (
                    loc, openweathermap.get_current_weather_data(
                        latitude=loc.latitude, longitude=loc.longitude, units=openweathermap.MeasurementUnits.METRIC
                    )
                )
                for loc in locations_page.object_list
            ]
        except OpenweathermapApiHTTPResponseError:
            messages.error(request, API_ERROR_MSG, fail_silently=True)
            logger.exception('External service error while serving request for %s', request.user.username)
            return render(request, tmpl_name, {'location_search_form': self.location_search_form})
        return render(
            request, tmpl_name, {
                'locations_page': locations_page, 'locations_weather': locations_weather,
                'location_search_form': self.location_search_form
            }
        )


class LocationsView(LoginRequiredMixin, View):
    location_search_form = LocationSearchForm

    def get(self, request):
        lname = request.GET.get('name')

        if lname is None:
            return render(
                request, 'weather/locations.html', {
                    'locations_list': [], 'location_search_form': self.location_search_form
                }
            )
        try:
            ldtos = openweathermap.get_locations_by_name(lname)
        except OpenweathermapApiHTTPResponseError:
            messages.error(request, API_ERROR_MSG, fail_silently=True)
            logger.exception('External service error while serving request for %s', request.user.username)
            return render(request, 'weather/locations.html', {'location_search_form': self.location_search_form})

        db_locations_list = list(Location.objects.filter(name__icontains=lname))

        api_locations_list = [
            Location(
                name=dto.name, latitude=dto.latitude, longitude=dto.longitude,
                local_names=dto.local_names, country=dto.country
            )
            for dto in ldtos
            if (lati_rounder(dto.latitude), longi_rounder(dto.longitude))
            not in [(lati_rounder(loc.latitude), longi_rounder(loc.longitude)) for loc in db_locations_list]
        ]

        logger.debug('%s request for locations with name "%s": '
                     'received %s locations from DB and %s from API (%s were moved as they already in DB)',
                     request.user.username, lname, len(db_locations_list),
                     len(api_locations_list), len(db_locations_list) - len(api_locations_list))

        locations_list = api_locations_list + db_locations_list
        locations_list.sort(key=lambda m: m.name)

        if not SAVE_LOCATIONS_ONLY_WHEN_ADDED_BY_USER:
            for lmodel in api_locations_list:
                lmodel.save()

        request.session['lately_requested_locations'] = [
            m.id if m.id is not None else model_to_dict(
                m, fields=['name', 'latitude', 'longitude', 'local_names', 'country']
            )
            for m in locations_list
        ]
        return render(
            request, 'weather/locations.html', {
                'locations_list': locations_list, 'location_search_form': self.location_search_form
            }
        )

    def post(self, request):
        lately_requested_locations = request.session.get('lately_requested_locations')
        selected_location_no: str = request.POST.get('location')
        try:
            if any(
                    [
                        lately_requested_locations is None, selected_location_no is None,
                        not selected_location_no.isnumeric()
                    ]
            ) or not 0 <= int(selected_location_no) < len(lately_requested_locations):
                messages.error(request, 'There was an error in your request. Please try again.', fail_silently=True)
                return render(request, 'weather/locations.html', {'location_search_form': self.location_search_form})

            selected_location = lately_requested_locations[int(selected_location_no)]
            if type(selected_location) is int:
                selected_location_model = Location.objects.get(pk=selected_location)
            else:
                selected_location_model = Location.objects.create(**selected_location)

            m2m_linkage = UserLocation(user=request.user, location=selected_location_model)

            if not UserLocation.objects.filter(user=m2m_linkage.user, location=m2m_linkage.location).exists():
                m2m_linkage.save()
                logger.info(
                    'User %s added location %s (id %s, %s, lat: %s, lon: %s)',
                    request.user.username, selected_location_model.name,
                    selected_location.id, selected_location.country,
                    selected_location_model.latitude, selected_location.longitude,
                )
        finally:
            with contextlib.suppress(KeyError):
                del request.session['lately_requested_locations']

        return HttpResponseRedirect('/')


class LocationRemoveView(LoginRequiredMixin, View):
    redirect_field_name = None

    def post(self, request):
        try:
            user_location_id: str = int(request.POST.get('id'))
        except (ValueError, TypeError):
            return HttpResponseBadRequest("Id should be a digit.")
        if not user_location_id:
            return HttpResponseRedirect('/')

        m2m_linkage = get_object_or_404(
            UserLocation, user=request.user, location_id=user_location_id
        )
        m2m_linkage.delete()
        logger.info(
            'User %s removed location %s (id %s, %s, lat: %s, lon: %s)',
            request.user.username, m2m_linkage.location.name,
            m2m_linkage.location.id, m2m_linkage.location.country,
            m2m_linkage.location.latitude, m2m_linkage.location.longitude,
        )
        return HttpResponseRedirect('/')
