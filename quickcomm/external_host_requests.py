


# This file deals with calling other API endpoints and returning the results in
# a dictionary format. This file also deals with the weirdness of pagination
# and caching external requests.

import requests_cache
import logging

# This caches the requests for 5 minutes, but this can be changed
session = requests_cache.CachedSession('external_cache', expire_after=300)

class BaseQCRequest:
    """This class is used to make requests to other servers. It is used to
    make requests to other servers, and to cache the results of those requests.
    This class is meant to be extended by other classes that will make requests
    to specific servers."""

    AUTHORS_ENDPOINT = '/authors'
    POSTS_ENDPOINT = '/posts'
    COMMENTS_ENDPOINT = '/comments'
    POST_LIKES_ENDPOINT = '/likes'
    COMMENT_LIKES_ENDPOINT = '/likes'
    FOLLOWERS_ENDPOINT = '/followers'

    def __init__(self, host, deserializers):
        """Initialize the request object. This will set the host and the
        session to use for the requests."""

        self.host_obj = host
        self.host = host.url
        if self.host[-1] == '/':
            self.host = self.host[:-1]
        self.session = session
        self.auth = host.username_password_base64
        self.deserializers = deserializers

    def map_list_authors(self ,data):
        raise NotImplementedError

    def map_raw_author(self, raw_author):
        raise NotImplementedError

    def map_raw_post(self, raw_post):
        raise NotImplementedError

    def map_list_posts(self, data):
        raise NotImplementedError

    def map_list_comments(self, data):
        raise NotImplementedError

    def map_raw_comment(self, raw_comment):
        raise NotImplementedError

    def map_list_post_likes(self, data):
        raise NotImplementedError

    def map_raw_post_like(self, raw_post_like):
        raise NotImplementedError

    def map_list_comment_likes(self, data):
        raise NotImplementedError

    def map_raw_comment_like(self, raw_comment_like):
        raise NotImplementedError

    def map_list_followers(self, data):
        raise NotImplementedError

    def map_raw_follower(self, raw_follower):
        raise NotImplementedError

    def map_raw_author_singular(self, raw_author):
        return self.map_raw_author(raw_author)

    def map_raw_post_singular(self, raw_post):
        return self.map_raw_post(raw_post)

    def map_raw_comment_singular(self, raw_comment):
        return self.map_raw_comment(raw_comment)

    def map_raw_post_like_singular(self, raw_post_like):
        return self.map_raw_post_like(raw_post_like)

    def map_raw_comment_like_singular(self, raw_comment_like):
        return self.map_raw_comment_like(raw_comment_like)

    def map_raw_follower_singular(self, raw_follower):
        return self.map_raw_follower(raw_follower)

    # TODO get list response function

    def get_singular_response(self, deserializer, endpoint, map_func, ensure_success=True):

        logging.info(f'Getting {endpoint}.')
        response = session.get(endpoint, headers={'Authorization':f'Basic {self.auth}'})

        # check response code
        if ensure_success and response.status_code != 200:
            logging.error(f'Response code for {endpoint} was not successful.')
            return

        try:
            json_response = response.json()
        except Exception as e:
            logging.error('Could not parse response as JSON.', exc_info=True)
            return

        try:
            mapped_item = map_func(json_response)
        except Exception as e:
            logging.error('Could not map item.', exc_info=True)
            return

        serialized_item = deserializer(data=mapped_item)

        try:
            serialized_item.is_valid(raise_exception=True)
        except Exception as e:
            logging.error('Could not validate item.', exc_info=True)
            return

        try:
            serialized_item.save(host=self.host_obj)
        except Exception as e:
            logging.error('Could not save item.', exc_info=True)
            return

    def get_paginated_response(self, deserializer, endpoint, map_func, list_base_func, check_author=[], **kwargs):

        logging.info(f'Getting {endpoint} with pagination.')


        empty = False
        page = 1

        while not empty:

            # call api
            response = session.get(endpoint, params={'page': page, 'size': 100}, headers={'Authorization':f'Basic {self.auth}'})
            logging.debug('Called endpoint for page ' + str(page) + '.')

            # check response code
            if response.status_code != 200:
                logging.info('Response code was not 200. Assuming empty and ending loop.')
                empty = True
                break

            try:
                json_response = response.json()
            except Exception as e:
                logging.error('Could not parse response as JSON.', exc_info=True)
                empty = True
                break

            # loop though authors
            try:
                current_raw_items = list_base_func(json_response)
            except Exception as e:
                logging.error('Could not get list of authors from JSON response.', exc_info=True)
                empty = True
                break

            if len(current_raw_items) == 0:
                logging.info('No more authors. Ending loop.')
                empty = True
                break


            for item in current_raw_items:

                extra_kwargs = {}
                for author_item in check_author:

                    if author_item == '':
                        raw_author = item
                        author_item = 'author'
                    else:
                        if item.get(author_item, None) is None:
                            logging.info('Author not in item. Skipping.')
                            continue
                        raw_author = item[author_item]

                    author = self.return_single_item(raw_author, self.map_raw_author, self.deserializers.author,
                         )
                    if author is None:
                        logging.info('Author was not valid. Skipping.')
                        continue
                    extra_kwargs[author_item] = author

                self.return_single_item(item, map_func, deserializer, **extra_kwargs, **kwargs)


            page += 1

    def return_single_item(self, item, map_func, deserializer, **kwargs):
        try:
            mapped_item = map_func(item)
        except Exception as e:
            logging.error('Could not map author.', exc_info=True)
            return
        serialized_item = deserializer(data=mapped_item)
        try:
            serialized_item.is_valid(raise_exception=True)
        except Exception as e:
            logging.error('Could not validate author.', exc_info=True)
            return None
        try:
            return serialized_item.save(**kwargs)
        except Exception as e:
            logging.error('Could not save author.', exc_info=True)
            return None
