from pyexpat.errors import messages
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.utils.html import format_html

from quickcomm.external_host_deserializers import sync_authors, sync_comment_likes, sync_comments, sync_post_likes, sync_posts, sync_followers

# Register your models here.

from .models import Author, CommentLike, Host, HostAuthenticator, Post, Comment, Follow, Like, RegistrationSettings, Inbox

admin.site.register(Follow)
admin.site.register(Like)
admin.site.register(Inbox)
admin.site.register(RegistrationSettings)
admin.site.register(CommentLike)

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('comment', 'author', 'post')
    readonly_fields = ('external_url', 'published')
    actions_on_top = True
    actions = ['sync_likes', 'clear_likes']

    def has_add_permission(self, request, obj=None):
        return True

    def has_change_permission(self, request, obj: Comment=None):
        if obj is None:
            return True

        if obj.author.is_local:
            return True

        if '_sync_likes' in request.POST or '_clear_likes' in request.POST:
            return True

        return False

    @admin.action(description='Sync Likes')
    def sync_likes(self, request, queryset):
        for comment in queryset:
            if comment.author.is_local:
                continue
            sync_comment_likes(comment)

        self.message_user(request, "Likes synced successfully")
        return HttpResponseRedirect(".")

    @admin.action(description='Clear Likes')
    def clear_likes(self, request, queryset):
        for comment in queryset:
            if comment.author.is_local:
                continue
            comment.likes.all().delete()

        self.message_user(request, "Likes cleared successfully")
        return HttpResponseRedirect(".")


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'published', 'visibility', 'unlisted')
    readonly_fields = ('external_url',)
    actions_on_top = True
    actions = ['sync_comments', 'clear_comments', 'sync_likes', 'clear_likes']
    # inlines = [CommentInlineForPost]

    # change_form_template = 'admin/edit_post.html'

    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'author','content_type', 'content', 'categories', 'visibility', 'unlisted'
                       )
        }),
        ('HOST INFORMATION', {
            'fields': ('external_url', 'source', 'origin')})
    )



    def has_add_permission(self, request, obj=None):
        return True

    # TODO fix permissions for HTML button actions
    def has_change_permission(self, request, obj: Post=None):
        if obj is None:
            return True

        if obj.author.is_local:
            return True

        if '_sync_comments' in request.POST or '_clear_comments' in request.POST:
            return True

        return False

    @admin.action(description='Sync Likes')
    def sync_likes(self, request, queryset):
        for post in queryset:
            if post.author.is_local:
                continue
            sync_post_likes(post)

        self.message_user(request, "Likes synced successfully")
        return HttpResponseRedirect(".")

    @admin.action(description='Clear Likes')
    def clear_likes(self, request, queryset):
        for post in queryset:
            if post.author.is_local:
                continue
            post.likes.all().delete()

        self.message_user(request, "Likes cleared successfully")
        return HttpResponseRedirect(".")

    @admin.action(description='Sync Comments')
    def sync_comments(self, request, queryset):
        for post in queryset:
            if post.author.is_local:
                continue
            sync_comments(post)

        self.message_user(request, "Comments synced successfully")
        return HttpResponseRedirect(".")

    @admin.action(description='Clear Comments')
    def clear_comments(self, request, queryset):
        for post in queryset:
            if post.author.is_local:
                continue
            post.comments.all().delete()

        self.message_user(request, "Comments cleared successfully")
        return HttpResponseRedirect(".")
@admin.register(HostAuthenticator)
class HostAuthenticatorAdmin(admin.ModelAdmin):
    list_display = ('username', 'nickname')
    readonly_fields = ('base64',)
    actions_on_top = True

    @admin.display(description='Base64 Encoded Username:Password')
    def base64(self, obj: HostAuthenticator):
        return obj.base64string
class PostInlineForAuthor(admin.TabularInline):
    model = Post
    extra = 0
    fields = ['title', 'description']
    show_change_link = True
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description='Title')
    def title(self, obj: Post):
        return obj.title


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'host', 'location')
    readonly_fields = ('host', 'external_url', 'location', 'profile_image_html')
    actions_on_top = True
    actions = ['sync_posts', 'clear_posts', 'sync_followers', 'clear_followers']
    inlines = [PostInlineForAuthor]

    change_form_template = 'admin/edit_author.html'

    fieldsets = (
        (None, {
            'fields': ('display_name', 'github', 'profile_image', 'profile_image_html', 'location')
        }),
        ('Host Details', {
            'fields': ('host', 'external_url')
        }),
    )

    @admin.display(description='Display Name')
    def display_name(self, obj: Author):
        return obj.display_name

    @admin.display(description="Profile Image")
    def profile_image_html(self, obj: Author):
        if obj is None or obj.profile_image is None:
            return format(f"<p>No image found</p>")

        return format_html(f"<img src={obj.profile_image} width=100pt height=100pt />")


    @admin.display(description='Location of Author')
    def location(self, obj: Author):
        return obj.location


    def has_add_permission(self, request, obj=None):
        return True

    # TODO fix permissions for HTML button actions
    def has_change_permission(self, request, obj: Author=None):
        if obj is None:
            return True

        if obj.is_local:
            return True

        if '_sync_posts' in request.POST or '_clear_posts' in request.POST:
            return True

        return False

    @admin.action(description='Sync posts')
    def sync_posts(self, request, queryset):
        for author in queryset:
            if author.is_local:
                continue
            sync_posts(author)


    @admin.action(description='Clear posts')
    def clear_posts(self, request, queryset):
        for author in queryset:
            Post.objects.filter(author=author).delete()

    @admin.action(description='Sync Followers')
    def sync_followers(self, request, queryset):
        for author in queryset:
            if author.is_local:
                continue
            sync_followers(author)

    @admin.action(description='Clear Followers')
    def clear_followers(self, request, queryset):
        for author in queryset:
            author.followers.all().delete()

    # Taken from https://books.agiliq.com/projects/django-admin-cookbook/en/latest/custom_button.html
    def response_change(self, request, obj: Host):
        if "_sync_posts" in request.POST:
            if obj.is_local:
                self.message_user(request, f"Cannot sync posts for local author {obj}", level='ERROR')
                return HttpResponseRedirect(".")
            sync_posts(obj)
            self.message_user(request, f"Synced posts for author {obj}")
            return HttpResponseRedirect(".")
        elif "_clear_posts" in request.POST:
            if obj.is_local:
                self.message_user(request, f"Cannot clear posts for local author {obj}. This is dangerous and should only be used for external requests!", level='ERROR')
                return HttpResponseRedirect(".")
            Post.objects.filter(author=obj).delete()
            self.message_user(request, f"Cleared posts for author {obj}")
            return HttpResponseRedirect(".")

        return super().response_change(request, obj)

class AuthorInlineForHost(admin.TabularInline):
    model = Author
    extra = 0
    fields = ['display_name', 'external_url']
    show_change_link = True
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description='Display Name')
    def display_name(self, obj: Author):
        return obj.display_name

@admin.register(Host)
class HostAdmin(admin.ModelAdmin):
    list_display = ('nickname_or_url', 'url', 'last_ping_result')
    readonly_fields = ('last_successful_ping', 'last_ping', 'last_ping_result')
    actions_on_top = True
    actions = ['ping']
    inlines = [AuthorInlineForHost]

    change_form_template = 'admin/edit_host.html'

    fieldsets = (
        (None, {
            'description': 'A host is a remote server that follows the CMPUT 404 Social Distribution protocol.',
            'fields': ('url', 'nickname', 'username_password_base64')
        }),
        ('Ping Details', {
            'classes': ('collapse'),
            'description': 'These fields are automatically updated when the host is pinged. The host is pinged occasionally in the background to check if it is still online, and when it is added or edited.',
            'fields': ('last_successful_ping', 'last_ping', 'last_ping_result')
        }),
    )

    @admin.display(description='Host')
    def nickname_or_url(self, obj: Host):
        return obj.nickname_or_url

    @admin.action(description='Ping')
    def ping(self, request, queryset):
        for host in queryset:
            host.ping()
        # save the hosts
        queryset.update()
        self.message_user(request, f"Pinged {queryset.count()} hosts")

    @admin.action(description='Sync author details')
    def sync_author_details(self, request, queryset):
        for host in queryset:
            sync_authors(host)

    @admin.action(description='Clear authors')
    def clear_authors(self, request, queryset):
        for host in queryset:
            Author.objects.filter(host=host).delete()

    # Taken from https://books.agiliq.com/projects/django-admin-cookbook/en/latest/custom_button.html
    def response_change(self, request, obj: Host):
        if "_ping" in request.POST:
            obj.ping()
            self.message_user(request, f"Pinged host {obj}")
            return HttpResponseRedirect(".")
        elif "_sync_authors" in request.POST:
            sync_authors(obj)
            self.message_user(request, f"Synced authors for host {obj}")
            return HttpResponseRedirect(".")
        elif "_clear_authors" in request.POST:
            Author.objects.filter(host=obj).delete()
            self.message_user(request, f"Cleared authors for host {obj}")
            return HttpResponseRedirect(".")

        return super().response_change(request, obj)
