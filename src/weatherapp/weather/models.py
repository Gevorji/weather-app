import datetime
from functools import wraps, partial

from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User


def get_max_min_value_validator(_min: int | float, _max: int | float, *, include_max=False, include_min=False):
    import operator
    min_comparator = operator.ge if include_min else operator.gt
    max_comparator = operator.le if include_max else operator.lt

    @wraps(get_max_min_value_validator)
    def validator(value):
        if not (min_comparator(value, _min) and max_comparator(value, _max)):
            raise ValidationError(
                'The value of this field should be between {0} and {1}'.format(
                    f'{_min}{" (included)" if include_min else ""}', f'{_max} {" (included)" if include_max else ""}'
                )
            )

    return validator


lati_rounder = partial(round, ndigits=4)
longi_rounder = lati_rounder


class Location(models.Model):
    name = models.CharField(max_length=50)
    users = models.ManyToManyField(User, through='UserLocation')
    latitude = models.FloatField(
        blank=False,
        validators=[get_max_min_value_validator(-90, 90, include_max=True, include_min=True)]
    )
    longitude = models.FloatField(
        blank=False, validators=[get_max_min_value_validator(-180, 180, include_max=True, include_min=True)]
    )
    local_names = models.JSONField(null=True, blank=True)
    country = models.CharField(max_length=30, null=True)


class UserLocation(models.Model):

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'location'], name='unique_user_location')
        ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    date_added = models.DateTimeField(default=datetime.datetime.now)
