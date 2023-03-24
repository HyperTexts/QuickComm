


# This file deals with calling other API endpoints and returning the results in
# a dictionary format. This file also deals with the weirdness of pagination
# and caching external requests.

from rest_framework import exceptions
import requests_cache
import logging
from requests.adapters import HTTPAdapter


from urllib3 import Retry

from quickcomm.models import Comment, Inbox, Post
from .request_exposer import get_request

# This caches the requests for 5 minutes, but this can be changed
session = requests_cache.CachedSession('external_cache', expire_after=1)
retry = Retry(connect=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)
class BaseQCRequest:
    """This class is used to make requests to other servers. It is used to
    make requests to other servers, and to cache the results of those requests.
    This class is meant to be extended by other classes that will make requests
    to specific servers."""

    PAGINATED_SIZE = 100

    AUTHORS_ENDPOINT = '/authors'
    POSTS_ENDPOINT = '/posts'
    COMMENTS_ENDPOINT = '/comments'
    POST_LIKES_ENDPOINT = '/likes'
    COMMENT_LIKES_ENDPOINT = '/likes'
    FOLLOWERS_ENDPOINT = '/followers'
    INBOX_ENDPOINT = '/inbox/'

    paginate_posts = True
    paginate_followers = True
    paginate_post_likes = True
    paginate_comment_likes = True

    def __init__(self, host, deserializers, serializers):
        """Initialize the request object. This will set the host and the
        session to use for the requests."""

        self.host_obj = host
        if host is not None:
            self.host = host.url
            if self.host[-1] == '/':
                self.host = self.host[:-1]
            self.auth = host.username_password_base64
        self.deserializers = deserializers
        self.serializers = serializers

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

    # INBOUND INBOX ITEMS MAPS

    def map_inbound_post_object(self, raw_post):
        raise NotImplementedError

    def map_inbound_post_author(self, raw_post):
        raise NotImplementedError

    def map_inbound_like_object(self, raw_like):
        raise NotImplementedError

    def map_inbound_like_author(self, raw_like):
        raise NotImplementedError

    def map_inbound_like_object_url(self, raw_like):
        raise NotImplementedError

    def map_inbound_comment_object(self, raw_comment):
        raise NotImplementedError

    def map_inbound_comment_author(self, raw_comment):
        raise NotImplementedError

    def map_inbound_comment_object_url(self, raw_comment):
        raise NotImplementedError

    def map_inbound_follow_object(self, raw_follow):
        raise NotImplementedError

    def map_inbound_follow_author(self, raw_follow):
        raise NotImplementedError

    # OUTBOUND INBOX ITEMS MAPS

    def map_outbound_post(self, activity_data):
        raise NotImplementedError

    def map_outbound_like(self, activity_data):
        raise NotImplementedError

    def map_outbound_comment(self, activity_data):
        raise NotImplementedError

    def map_outbound_follow(self, activity_data):
        raise NotImplementedError

    def _clean_url(self, url):
        if url[-1] == '/':
            return url[:-1]
        return url

    def _get_singular_response(self, deserializer, endpoint, map_func, ensure_success=True):

        logging.info(f'Getting {endpoint}.')
        try:
            response = session.get(endpoint, headers={'Authorization':f'Basic {self.auth}'})
        except Exception as e:
            logging.warning(f'Could not get {endpoint}, skipping.', exc_info=True)
            return

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

    def _get_list_response(self, deserializer, endpoint, map_func, list_base_func, check_author=[], paginated=True, **kwargs):

        logging.info(f'Getting {endpoint} with pagination.')

        empty = False
        page = 1

        while not empty:

            if paginated:
                # call api
                try:
                    response = session.get(endpoint, params={'page': page, 'size': self.PAGINATED_SIZE}, headers={'Authorization':f'Basic {self.auth}'})
                    logging.debug('Called endpoint for page ' + str(page) + '.')
                except Exception as e:
                    logging.warning(f'Could not connect to {endpoint}, skipping.')
                    break

                # check response code
                if response.status_code != 200:
                    logging.info('Response code was not 200. Assuming empty and ending loop.')
                    empty = True
                    break
            else:
                response = session.get(endpoint, headers={'Authorization':f'Basic {self.auth}'})
                empty = True

                # check response code
                if response.status_code != 200:
                    logging.info('Response code was not 200. This endpoint is not paginated so some error occured.')
                    break

                logging.debug('Called endpoint for page ' + str(page) + '.')

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

                    author = self._return_single_item(raw_author, self.map_raw_author, self.deserializers.author,
                         )
                    if author is None:
                        logging.info('Author was not valid. Skipping.')
                        continue
                    extra_kwargs[author_item] = author

                self._return_single_item(item, map_func, deserializer, **extra_kwargs, **kwargs)


            page += 1

    def _send_to_inbox(self, author, item, serializer, map_func):
        logging.info(f'Sending {item} to inbox of {author}.')
        endpoint = f'{self._clean_url(author.external_url)}{self.INBOX_ENDPOINT}'
        serialized_item = serializer(item, context={'request': get_request()})
        data = map_func(serialized_item.data)
        res = session.post(endpoint, json=data, headers={'Authorization':f'Basic {self.auth}'},
            )
        try:
            res.raise_for_status()
        except Exception as e:
            logging.error(f'Could not send {item} to inbox of {author}.', exc_info=True)
            return False
        return True

    def _return_single_item(self, item, map_func, deserializer, **kwargs):
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
        return self._get_list_response(self.deserializers.author,
            self._clean_url(self.host) + self.AUTHORS_ENDPOINT,
        self.map_raw_author, self.map_list_authors,
        host=self.host_obj,
        paginated=True
        )

    def update_author(self, full_author_url):
        return self._get_singular_response(self.deserializers.author,
            full_author_url,
            self.map_raw_author_singular
            )

    def update_posts(self, author):

        # Update the author first from the data given in the post
        return self._get_list_response(self.deserializers.post,
            self._clean_url(author.external_url) + self.POSTS_ENDPOINT,
            self.map_raw_post, self.map_list_posts,
            author=author,
            paginated=self.paginate_posts
            )

    def update_comments(self, post):
        return self._get_list_response(self.deserializers.comment,
            self._clean_url(post.external_url) + self.COMMENTS_ENDPOINT,
            self.map_raw_comment, self.map_list_comments,
            check_author=["author"],
            post=post,
            paginated=True
            )

    def update_post_likes(self, post):
        return self._get_list_response(self.deserializers.post_like,
            self._clean_url(post.external_url) + self.POST_LIKES_ENDPOINT,
            self.map_raw_post_like, self.map_list_post_likes,
            check_author=["author"],
            post=post,
            paginated=self.paginate_post_likes
            )

    def update_comment_likes(self, comment):
        return self._get_list_response(self.deserializers.comment_like,
            self._clean_url(comment.external_url) + self.COMMENT_LIKES_ENDPOINT,
            self.map_raw_comment_like, self.map_list_comment_likes,
            check_author=["author"],
            comment=comment,
            paginated=self.paginate_comment_likes
            )

    def update_followers(self, author):
        return self._get_list_response(self.deserializers.follower,
            self._clean_url(author.external_url) + self.FOLLOWERS_ENDPOINT,
            self.map_raw_follower, self.map_list_followers,
            check_author=[''],
            following=author,
            paginated=True
            )

    def send_post(self, post, author):
        return self._send_to_inbox(author, post, self.serializers.post, self.map_outbound_post)

    def send_comment(self, comment, author):
        return self._send_to_inbox(author, comment, self.serializers.comment, self.map_outbound_comment)

    def send_post_like(self, post_like, author):
        return self._send_to_inbox(author, post_like, self.serializers.post_like, self.map_outbound_like)

    def send_comment_like(self, comment_like, author):
        return self._send_to_inbox(author, comment_like, self.serializers.comment_like, self.map_outbound_like)

    def send_follow(self, follow, author):
        return self._send_to_inbox(author, follow, self.serializers.follow, self.map_outbound_follow)

    def import_base(self, data, map_author, map_inbound_object, map_object, deserializer, **kwargs):
        raw_author = map_author(data)
        author = self._return_single_item(raw_author, self.map_raw_author, self.deserializers.author)
        if author is None:
            logging.info('Author was not valid')
            raise exceptions.ValidationError('Author was not valid')

        raw_object = map_inbound_object(data)
        obj = self._return_single_item(raw_object, map_object, deserializer, author=author, **kwargs)
        if obj is None:
            logging.info('Object was not valid')
            raise exceptions.ValidationError('Object was not valid')

        return obj


    def import_follow(self, data):

        raw_follower = self.map_inbound_follow_author(data)
        follower = self._return_single_item(raw_follower, self.map_raw_author, self.deserializers.author)
        if follower is None:
            logging.info('Follower was not valid')
            raise exceptions.ValidationError('Follower was not valid')

        raw_following = self.map_inbound_follow_object(data)
        following = self._return_single_item(raw_following, self.map_raw_author, self.deserializers.author)
        if following is None:
            logging.info('Following was not valid')
            raise exceptions.ValidationError('Following was not valid')

        follower = self._return_single_item({}, self.map_raw_follower, self.deserializers.follower, author=follower, following=following, request=True)
        if follower is None:
            logging.info('Follower was not valid')
            raise exceptions.ValidationError('Follower was not valid')

        return follower


    def import_inbox_item(self, data):
        # lowercase the type
        data['type'] = data['type'].lower()

        if data['type'] == 'post':
            logging.debug("Inbox item type is post")
            return self.import_base(data, self.map_inbound_post_author, self.map_inbound_post_object, self.map_raw_post, self.deserializers.post), Inbox.InboxType.POST
        elif data['type'] == 'like':
            object_url = self.map_inbound_like_object_url(data)

            if 'comments' in object_url.split('/'):
                logging.debug("Inbox item type is comment like")
                comment = Comment.get_from_url(object_url)
                if comment is None:
                    logging.info('Comment was not valid')
                    raise exceptions.ValidationError('Comment was not valid')
                return self.import_base(data, self.map_inbound_like_author, self.map_inbound_like_object, self.map_raw_comment_like,
                self.deserializers.comment_like, comment=comment), Inbox.InboxType.COMMENTLIKE

            logging.debug("Inbox item type is post like")
            post = Post.get_from_url(object_url)
            if post is None:
                logging.info('Post was not valid')
                raise exceptions.ValidationError('Post was not valid')
            return self.import_base(data, self.map_inbound_like_author, self.map_inbound_like_object, self.map_raw_post_like,
            self.deserializers.post_like, post=post), Inbox.InboxType.LIKE

        elif data['type'] == 'comment':
            logging.debug("Inbox item type is comment")
            object_url = self.map_inbound_comment_object_url(data)
            post = Post.get_from_url(object_url)
            if post is None:
                logging.info('Post was not valid')
                raise exceptions.ValidationError('Post was not valid')

            return self.import_base(data, self.map_inbound_comment_author, self.map_inbound_comment_object, self.map_raw_comment,
            self.deserializers.comment, post=post), Inbox.InboxType.COMMENT

        elif data['type'] == 'follow':
            logging.debug("Inbox item type is follow request")
            return self.import_follow(data), Inbox.InboxType.FOLLOW

        raise exceptions.ValidationError('Type not supported')


class THTHQCRequest(BaseQCRequest):
    # TODO for export, make it in

    paginate_posts = True
    paginate_followers = False
    paginate_post_likes = False
    paginate_comment_likes = False

    def set_null_to_empty_string(self, data):
        for key, value in data.items():

            # nest the loop
            if isinstance(value, dict):
                self.set_null_to_empty_string(value)
                continue

            if value is None:
                data[key] = ''

    def map_raw_author(self, external_data):
        return {
            'type': external_data['type'],
            'external_url': external_data['url'],
            'display_name': f"Undefined display name ({external_data['url']})" if external_data['displayName'] == '' else external_data['displayName'],
            'profile_image': None if external_data['profileImage'] == '' else external_data['profileImage'],
            'github': None if external_data['github'] == '' else external_data['github'],
                }


    def map_raw_post(self, raw_post):

        # split hex data based on type
        if raw_post['contentType'] == 'image/png;base64' or raw_post['contentType'] == 'image/jpeg;base64':
            raw_post['content'] = raw_post['content'].split(',')[1]


        return {
            'type': raw_post['type'],
            'title': f"Undefined title ({raw_post['id']})" if raw_post['title'] == '' else raw_post['title'],
            'external_url': raw_post['id'],
            'source': raw_post['id'] if raw_post['source'] == '' else raw_post['source'],
            'origin': raw_post['id'] if raw_post['origin'] == '' else raw_post['origin'],
            'description': f"Undefined description ({raw_post['id']})" if raw_post['description'] == '' else raw_post['description'],
            'content': f"Undefined content ({raw_post['id']})" if raw_post['content'] == '' else raw_post['content'],
            'content_type': raw_post['contentType'],
            'published': raw_post['published'],
            'visibility': raw_post['visibility'],
            'unlisted': raw_post['unlisted'],
        }

    def map_raw_comment(self, raw_comment):
        return {
            'type': raw_comment['type'],
            'external_url': raw_comment.get('id', None),
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
        return data['items']

    def map_list_posts(self, data):
        return data['items']

    def map_list_comments(self, data):
        return data['items']

    def map_list_post_likes(self, data):
        return data['items']

    def map_list_comment_likes(self, data):
        return data['items']

    def map_list_followers(self, data):
        return data['items']

    def map_inbound_post_object(self, raw_post):
        return raw_post['object']

    def map_inbound_post_author(self, raw_post):
        return raw_post['author']

    def map_inbound_comment_object(self, raw_comment):
        if raw_comment['comment'].get('id', False):
            # remove this property, we will be making a new comment
            del raw_comment['comment']['id']

        return raw_comment['comment']

    def map_inbound_comment_object_url(self, raw_comment):
        return raw_comment['object']

    def map_inbound_comment_author(self, raw_comment):
        return raw_comment['actor']

    def map_inbound_like_object_url(self, raw_like):
        return raw_like['object']

    def map_inbound_like_author(self, raw_like):
        return raw_like['actor']

    def map_inbound_like_object(self, raw_like):
        return raw_like

    def map_inbound_follow_object(self, raw_follow):
        return raw_follow['object']

    def map_inbound_follow_author(self, raw_follow):
        return raw_follow['actor']

    def map_outbound_post(self, activity_data):

        # lowercase the type
        activity_data['type'] = activity_data['type'].lower()

        # # can't have null values in the json post
        self.set_null_to_empty_string(activity_data)

        return activity_data

    def map_outbound_comment(self, activity_data):

            # lowercase the type
            activity_data['type'] = activity_data['type'].lower()

            # can't have null values in the json post
            self.set_null_to_empty_string(activity_data)

            return activity_data

    def map_outbound_like(self, activity_data):
            activity_data['type'] = activity_data['type'].lower()

            # can't have null values in the json post
            self.set_null_to_empty_string(activity_data)

            return activity_data

    def map_outbound_follow(self, activity_data):
            activity_data['type'] = activity_data['type'].lower()

            # can't have null values in the json post
            self.set_null_to_empty_string(activity_data)

            return activity_data

class InternalQCRequest(BaseQCRequest):

    def map_raw_author(self, external_data):
        return {
            'type': external_data['type'],
            'external_url': external_data['url'],
            'display_name': external_data['displayName'],
            'profile_image': external_data['profileImage'],
            'github': external_data['github'],
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
            'external_url': raw_comment.get('id', None),
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
        return data['items']

    def map_list_posts(self, data):
        return data['items']

    def map_list_comments(self, data):
        return data['comments']

    def map_list_post_likes(self, data):
        return data['items']

    def map_list_comment_likes(self, data):
        return data['items']

    def map_list_followers(self, data):
        return data['items']

    def map_inbound_post_object(self, raw_post):
        return raw_post['object']

    def map_inbound_post_author(self, raw_post):
        return raw_post['author']

    def map_inbound_comment_object(self, raw_comment):
        if raw_comment['comment'].get('id', False):
            del raw_comment['comment']['id']

        if raw_comment['comment'].get('url', False):
            del raw_comment['comment']['url']

        return raw_comment['comment']

    def map_inbound_comment_author(self, raw_comment):
        return raw_comment['author']

    def map_inbound_comment_object_url(self, raw_comment):
        return raw_comment['object']

    def map_inbound_like_object_url(self, raw_like):
        return raw_like['object']

    def map_inbound_like_author(self, raw_like):
        return raw_like['author']

    def map_inbound_like_object(self, raw_like):
        return raw_like

    def map_inbound_follow_object(self, raw_follow):
        return raw_follow['object']

    def map_inbound_follow_author(self, raw_follow):
        return raw_follow['actor']

    def map_outbound_post(self, activity_data):
        return activity_data

    def map_outbound_comment(self, activity_data):
        return activity_data

    def map_outbound_like(self, activity_data):
        return activity_data

    def map_outbound_follow(self, activity_data):
        return activity_data

