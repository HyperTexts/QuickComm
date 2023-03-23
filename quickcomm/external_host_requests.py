


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

    def update_authors(self):
        return self.get_paginated_response(self.deserializers.author,
            self.host + self.AUTHORS_ENDPOINT,
        self.map_raw_author, self.map_list_authors,
        parent=self.host_obj
        )


    def update_posts(self, author):
        # Update the author first from the data given in the post
        return self.get_paginated_response(self.deserializers.post,
            author.external_url + self.POSTS_ENDPOINT,
            self.map_raw_post, self.map_list_posts,
            author=author)

    def update_comments(self, post):
        return self.get_paginated_response(self.deserializers.comment,
            post.external_url + self.COMMENTS_ENDPOINT,
            self.map_raw_comment, self.map_list_comments,
            check_author=["author"],
            post=post)

    def update_post_likes(self, post):
        return self.get_paginated_response(self.deserializers.post_like,
            post.external_url + self.POST_LIKES_ENDPOINT,
            self.map_raw_post_like, self.map_list_post_likes,
            check_author=["author"],
            post=post)

    def update_comment_likes(self, comment):
        return self.get_paginated_response(self.deserializers.comment_like,
            comment.external_url + self.COMMENT_LIKES_ENDPOINT,
            self.map_raw_comment_like, self.map_list_comment_likes,
            check_author=["author"],
            comment=comment)

    def update_followers(self, author):
        return self.get_paginated_response(self.deserializers.follower,
            author.external_url + self.FOLLOWERS_ENDPOINT,
            self.map_raw_follower, self.map_list_followers,
            check_author=[''],
            following=author)

class THTHQCRequest(BaseQCRequest):

    def map_raw_author(self, external_data):
        return {
            'type': external_data['type'],
            'external_url': external_data['url'],
            'display_name': external_data['displayName'],
            'profile_image': None if external_data['profileImage'] == '' else external_data['profileImage'],
            'github': None if external_data['github'] == '' else external_data['github'],
                }

    def map_raw_post(self, raw_post):
        return {
            'type': raw_post['type'],
            'title': raw_post['title'],
            'external_url': raw_post['id'],
            'source': raw_post['source'],
            'origin': raw_post['origin'],
            'description': raw_post['description'],
            'content': raw_post['content'],
            'content_type': raw_post['contentType'],
            'published': raw_post['published'],
            'visibility': raw_post['visibility'],
            'unlisted': raw_post['unlisted'],
        }

    def map_raw_comment(self, raw_comment):
        return {
            'type': raw_comment['type'],
            'external_url': raw_comment['id'],
            'comment': raw_comment['comment'],
            'content_type': raw_comment['contentType'],
            'published': raw_comment['published'],
        }

    def map_raw_post_like(self, raw_post_like):
        return {
            'type': raw_post_like['type'],
            'summary': raw_post_like['summary'],
        }

    def map_raw_comment_like(self, raw_comment_like):
        return {
            'type': raw_comment_like['type'],
            'summary': raw_comment_like['summary'],
        }

    def map_raw_follower(self, raw_follower):
        return {}

    def map_list_authors(self, data):
        return data

    def map_list_posts(self, data):
        return data

    def map_list_comments(self, data):
        return data

    def map_list_post_likes(self, data):
        return data

    def map_list_comment_likes(self, data):
        return data

    def map_list_followers(self, data):
        return data