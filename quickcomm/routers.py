
from rest_framework import routers
from rest_framework.routers import Route
from rest_framework_nested import routers as nested_routers
from django.urls import path
# This file contains the routers for the API. Routers are used to map HTTP methods
# to viewsets. They are similar to urls.py, but they are more flexible and allow
# for more complex mappings.

# The base code from this is taken from the rest_framework code, namely the
# SimpleRouter class. We override the routes to change the mappings.

class AuthorRouter(routers.SimpleRouter):
    routes = [
        # List route.
        Route(
            url=r'^{prefix}{trailing_slash}$',
            mapping={
                'get': 'list',
            },
            name='{basename}-list',
            detail=False,
            initkwargs={'suffix': 'List'}
        ),
        # Detail route.
        Route(
            url=r'^{prefix}/{lookup}{trailing_slash}$',
            mapping={
                'get': 'retrieve',
                'post': 'partial_update',
            },
            name='{basename}-detail',
            detail=True,
            initkwargs={'suffix': 'Instance'}
        ),
        # Inbox route.
        Route(
            url=r'^{prefix}/{lookup}/inbox{trailing_slash}$',
            mapping={
                'post': 'inbox',
            },
            name='{basename}-inbox',
            detail=False,
            initkwargs={'suffix': 'Inbox'}
        ),
    ]

class FollowersRouter(nested_routers.NestedSimpleRouter):
    routes = [
        # List route.
        Route(
            url=r'^{prefix}{trailing_slash}$',
            mapping={
                'get': 'list',
            },
            name='{basename}-list',
            detail=False,
            initkwargs={'suffix': 'List'}
        ),
        # Detail route.
        # FIXME HARDCODED, BAD! DON'T DO THIS
        Route(
            url=r'^{prefix}/(?P<pk>.+){trailing_slash}$',
            mapping={
                'get': 'retrieve',
            },
            name='{basename}-detail',
            detail=True,
            initkwargs={'suffix': 'Instance'}
        ),
    ]

# TODO paginate comment router
class CommentsRouter(nested_routers.NestedSimpleRouter):
    routes = [
        # List route.
        Route(
            url=r'^{prefix}{trailing_slash}$',
            mapping={
                'get': 'list',
                'post': 'create'
            },
            name='{basename}-list',
            detail=False,
            initkwargs={'suffix': 'List'}
        ),
        # Detail route.
        Route(
            url=r'^{prefix}/{lookup}{trailing_slash}$',
            mapping={
                'get': 'retrieve',
            },
            name='{basename}-detail',
            detail=True,
            initkwargs={'suffix': 'Instance'}
        ),
    ]

class InboxRouter(nested_routers.NestedSimpleRouter):
    routes = [
        # List route.
        Route(
            url=r'^{prefix}{trailing_slash}$',
            mapping={
                'post': 'create',
            },
            name='{basename}-list',
            detail=False,
            initkwargs={'suffix': 'List'}
        ),
    ]

class PostLikesRouter(nested_routers.NestedSimpleRouter):
    routes = [
        # List route.
        Route(
            url=r'^{prefix}{trailing_slash}$',
            mapping={
                'get': 'list',
            },
            name='{basename}-list',
            detail=False,
            initkwargs={'suffix': 'List'}
        ),
    ]

class CommentLikesRouter(nested_routers.NestedSimpleRouter):
    routes = [
        # List route.
        Route(
            url=r'^{prefix}{trailing_slash}$',
            mapping={
                'get': 'list',
            },
            name='{basename}-list',
            detail=False,
            initkwargs={'suffix': 'List'}
        ),
    ]

class AuthorLikedRouter(nested_routers.NestedSimpleRouter):
    routes = [
        # List route.
        Route(
            url=r'^{prefix}{trailing_slash}$',
            mapping={
                'get': 'list',
            },
            name='{basename}-list',
            detail=False,
            initkwargs={'suffix': 'List'}
        ),
    ]
class LikedRouter(nested_routers.NestedSimpleRouter):
    routes = [
        # List route.
        Route(
            url=r'^{prefix}{trailing_slash}$',
            mapping={
                'get': 'list',
            },
            name='{basename}-list',
            detail=False,
            initkwargs={'suffix': 'List'}
        ),
    ]



class PostRouter(nested_routers.NestedSimpleRouter):
    routes = [
        # List route.
        Route(
            url=r'^{prefix}{trailing_slash}$',
            mapping={
                'get': 'list',
                'post': 'create'
            },
            name='{basename}-list',
            detail=False,
            initkwargs={'suffix': 'List'}
        ),
        # Detail route.
        Route(
            url=r'^{prefix}/{lookup}{trailing_slash}$',
            mapping={
                'get': 'retrieve',
                'post': 'partial_update',
                'delete': 'destroy',
                'put': 'update',
            },
            name='{basename}-detail',
            detail=True,
            initkwargs={'suffix': 'Instance'}
        ),

        # Image route.
        Route(
            url=r'^{prefix}/{lookup}/image{trailing_slash}$',
            mapping={
                'get': 'image',
            },
            name='{basename}-image',
            detail=True,
            initkwargs={'suffix': 'Image'}
        ),
    ]