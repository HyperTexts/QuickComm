
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class BasePagination(PageNumberPagination):
    page_size_query_param = 'size'
    page_size = 10
    max_page_size = 1000
    url = None
    upper_response_param = None
    upper_url = None

    # TODO add id properly
    def get_paginated_response(self, data):
        mymap = {
            'id': self.url,
        }
        if self.upper_response_param and self.upper_url:
            mymap[self.upper_response_param] = self.upper_url

        mymap.update({'type': self.response_type,
            'page': self.page.number,
            'size': self.get_page_size(self.request),
            self.response_data_field: data })

        return Response(data=mymap)

class CommentsPagination(BasePagination):
    response_type = 'comments'
    response_data_field = 'comments'

class AuthorsPagination(BasePagination):
    response_type = 'authors'
    response_data_field = 'items'

class FollowersPagination(BasePagination):
    response_type = 'followers'
    response_data_field = 'items'

class PostsPagination(BasePagination):
    response_type = 'posts'
    response_data_field = 'items'

class PostLikesPagination(BasePagination):
    response_type = 'likes'
    response_data_field = 'items'

class CommentLikesPagination(BasePagination):
    response_type = 'likes'
    response_data_field = 'items'

class AuthorLikedPagination(BasePagination):
    response_type = 'liked'
    response_data_field = 'items'