from django.contrib import admin

# Register your models here.

from .models import Author, Post, Comment, Follow, Like
from .models import RegistrationSettings
from .forms import RegistrationSettingsForm

# allow admin to make new accounts inactive


class RegistrationSettingsAdmin(admin.ModelAdmin):
    form = RegistrationSettingsForm


admin.site.register(RegistrationSettings, RegistrationSettingsAdmin)


admin.site.register(Author)
admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(Follow)
admin.site.register(Like)
