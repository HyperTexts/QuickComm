from django.urls import path, re_path
from rest_framework.schemas import get_schema_view
from . import views
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from drf_yasg.generators import OpenAPISchemaGenerator

class Gen(OpenAPISchemaGenerator):
    """This is a custom schema generator that adds examples and descriptions to
    the schema. This is done this way so we can add examples and descriptions
    to the serializers, and not the views."""
    def get_schema(self, request=None, public=False):
        # adapted from https://github.com/axnsan12/drf-yasg/issues/129#issuecomment-1156837547
        schema = super().get_schema(request, public)
        for definition in schema.definitions.keys():

            if hasattr(schema.definitions[definition]._NP_serializer, "get_examples"):
                examples = schema.definitions[definition]._NP_serializer.get_examples()
                for example in examples.keys():
                    if example in schema.definitions[definition]["properties"]:
                        schema.definitions[definition]["properties"][example][
                            "example"
                        ] = examples[example]

            if hasattr(schema.definitions[definition]._NP_serializer, "get_descriptions"):
                descriptions = schema.definitions[definition]._NP_serializer.get_descriptions()
                for description in descriptions.keys():
                    if description in schema.definitions[definition]["properties"]:
                        schema.definitions[definition]["properties"][description][
                            "description"
                        ] = descriptions[description]
        return schema

schema_view = get_schema_view(
    openapi.Info(
      title="QuickComm API",
      default_version='0.0.1',
      description="A distributed social network.",
      license=openapi.License(name="Apache License 2.0"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
    generator_class=Gen,
)
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from drf_yasg.generators import OpenAPISchemaGenerator

class Gen(OpenAPISchemaGenerator):
    """This is a custom schema generator that adds examples and descriptions to
    the schema. This is done this way so we can add examples and descriptions
    to the serializers, and not the views."""
    def get_schema(self, request=None, public=False):
        # adapted from https://github.com/axnsan12/drf-yasg/issues/129#issuecomment-1156837547
        schema = super().get_schema(request, public)
        for definition in schema.definitions.keys():

            if hasattr(schema.definitions[definition]._NP_serializer, "get_examples"):
                examples = schema.definitions[definition]._NP_serializer.get_examples()
                for example in examples.keys():
                    if example in schema.definitions[definition]["properties"]:
                        schema.definitions[definition]["properties"][example][
                            "example"
                        ] = examples[example]

            if hasattr(schema.definitions[definition]._NP_serializer, "get_descriptions"):
                descriptions = schema.definitions[definition]._NP_serializer.get_descriptions()
                for description in descriptions.keys():
                    if description in schema.definitions[definition]["properties"]:
                        schema.definitions[definition]["properties"][description][
                            "description"
                        ] = descriptions[description]
        return schema

schema_view = get_schema_view(
    openapi.Info(
      title="QuickComm API",
      default_version='0.0.1',
      description="A distributed social network.",
      license=openapi.License(name="Apache License 2.0"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
    generator_class=Gen,
)

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('register/', views.register, name='register'),
    path('create/plain', views.create_post, name='create_plain'),
    path('create/markdown', views.create_markdown, name='create_markdown'),
    path('authors/', views.view_authors, name='view_authors'),
    path('authors/<uuid:author_id>/', views.view_profile, name='view_profile'),
    path('authors/<uuid:author_id>/posts', views.view_author_posts, name='view_author_posts'),
    path('authors/<uuid:author_id>/posts/<uuid:post_id>/', views.post_view, name='post_view'),
    path('authors/<uuid:author_id>/posts/<uuid:post_id>/post_liked', views.post_like, name='post_like'),
    path('authors/<uuid:author_id>/posts/<uuid:post_id>/post_comment', views.post_comment, name='post_comment'),
    path('authors/<uuid:author_id>/followers/', views.view_followers, name='view_followers'),
    path('create/image', views.create_image, name='create_image'),
    re_path(r'^openapi(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^openapi/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('send_follow_request/<uuid:author_id>/', views.send_follow_request, name='send_follow_request'),
    path('accept_request/<uuid:author_id>/', views.accept_request, name='accept_request'),
    path('authors/<uuid:author_id>/requests/', views.view_requests, name='view_requests'),
]
