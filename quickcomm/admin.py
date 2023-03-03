from django.contrib import admin

# Register your models here.

from .models import Author, Post, Comment, Follow, Like,follow_request

admin.site.register(Author)
admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(Follow)
admin.site.register(Like)
admin.site.register(follow_request)