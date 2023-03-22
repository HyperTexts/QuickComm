from django.contrib import admin
from django.http import HttpResponseRedirect
from django.utils.html import format_html

# Register your models here.

from .models import Author, CommentLike, Host, HostAuthenticator, Post, Comment, Follow, Like, RegistrationSettings, Inbox

# admin.site.register(Author)
admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(Follow)
admin.site.register(Like)
admin.site.register(Inbox)
admin.site.register(RegistrationSettings)
admin.site.register(CommentLike)

@admin.register(HostAuthenticator)
class HostAuthenticatorAdmin(admin.ModelAdmin):
    list_display = ('username', 'nickname')
    readonly_fields = ('base64',)
    actions_on_top = True

    @admin.display(description='Base64 Encoded Username:Password')
    def base64(self, obj: HostAuthenticator):
        return obj.base64string

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'host', 'location')
    readonly_fields = ('host', 'external_url', 'location', 'profile_image_html')
    actions_on_top = True
    # actions = ['sync_posts']


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


    # @admin.action(description='Sync posts')
    # def sync_posts(self, request, queryset):
    #     for author in queryset:
    #         author.sync_posts()
    #     self.message_user(request, f"Synced posts for {queryset.count()} authors")

    def has_add_permission(self, request, obj=None):
        return True

    def has_change_permission(self, request, obj: Author=None):
        if obj is None:
            return True

        if obj.is_local:
            return True

        return False


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
            'fields': ('url', 'nickname')
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
            host.sync_authors()

    # Taken from https://books.agiliq.com/projects/django-admin-cookbook/en/latest/custom_button.html
    def response_change(self, request, obj: Host):
        if "_ping" in request.POST:
            obj.ping()
            self.message_user(request, f"Pinged host {obj}")
            return HttpResponseRedirect(".")
        elif "_sync_authors" in request.POST:
            obj.sync_authors()
            self.message_user(request, f"Synced authors for host {obj}")
            return HttpResponseRedirect(".")

        return super().response_change(request, obj)
