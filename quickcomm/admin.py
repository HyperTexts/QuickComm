from django.contrib import admin

# Register your models here.

from .models import Author, Post, Comment, Follow, Like, RegistrationSettings

# allow admin to make new accounts inactive

admin.site.register(Author)
admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(Follow)
admin.site.register(Like)
admin.site.register(RegistrationSettings)
