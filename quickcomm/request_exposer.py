from django.conf import settings
from quickcomm import models

_request = None

def get_request():
    return _request

# taken from https://ruhshan-ahmed.medium.com/django-hack-how-to-access-request-object-from-models-6821d6107da
# to allow request data in models
def RequestExposerMiddleware(get_response):
    def middleware(request):
        global _request
        _request = request
        return get_response(request)

    return middleware