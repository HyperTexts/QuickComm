from django.contrib import admin
from django.http import HttpResponseRedirect

# Register your models here.

from .models import Author, Host, Post, Comment, Follow, Like, RegistrationSettings, Inbox

admin.site.register(Author)
admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(Follow)
admin.site.register(Like)
admin.site.register(Inbox)
admin.site.register(RegistrationSettings)

@admin.register(Host)
class HostAdmin(admin.ModelAdmin):
    list_display = ('nickname_or_url', 'url', 'last_ping_result')
    readonly_fields = ('last_successful_ping', 'last_ping', 'last_ping_result')
    actions_on_top = True
    actions = ['ping']

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

    # Taken from https://books.agiliq.com/projects/django-admin-cookbook/en/latest/custom_button.html
    def response_change(self, request, obj: Host):
        if "_ping" in request.POST:
            obj.ping()
            self.message_user(request, f"Pinged host {obj}")
            return HttpResponseRedirect(".")

        return super().response_change(request, obj)
