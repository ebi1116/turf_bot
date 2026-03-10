from django.contrib import admin
from .models import Area, Turf, Booking, UserSession

admin.site.register(Area)
admin.site.register(Turf)
admin.site.register(Booking)
admin.site.register(UserSession)