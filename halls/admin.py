from django.contrib import admin

# Register your models here.

from .models import Hall, Video

admin.site.register(Hall)
admin.site.register(Video)