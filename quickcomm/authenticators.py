import base64
from django.contrib.auth.models import User
from rest_framework import authentication
from rest_framework import exceptions
from rest_framework.request import Request

from quickcomm.models import HostAuthenticator

# This file contains a custom Basic authentication for HTTP that uses our
# HostAuthenticator model. This is used to authenticate requests from other
# servers. This also allows us to use these faux "API" keys or allow normal
# users to authenticate with their username and password.


class APIBasicAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request: Request):
        # get the username and password from the request as basic auth
        basic = request.META.get('HTTP_AUTHORIZATION', '').split()
        if not basic or basic[0].lower() != 'basic':
            return None


        # decode the username and password
        try:
            username, password = base64.b64decode(basic[1]).decode('utf-8').split(':')
        except:
            raise exceptions.AuthenticationFailed('Invalid authentication header')

        # check that the username and password are valid
        try:
            authenticator = HostAuthenticator.objects.get(username=username)
        except HostAuthenticator.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid username or password')

        if not authenticator.check_password(password):
            raise exceptions.AuthenticationFailed('Invalid username or password')

        return (authenticator, None)
