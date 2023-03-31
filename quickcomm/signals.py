
# This class dispatches external inbox items when they are added to the inbox.
# It uses the signal system to do this, as we cannot properly import the
# model serializers in the model classes.


def export_http_request_on_inbox_save(sender):

    # import here to avoid circular imports
    from quickcomm.external_host_deserializers import get_request_class_from_host
    from quickcomm.models import Inbox
    import logging

    logging.info(f"Inbox item added {sender}, sending to external host")

    # skip if the author is not external
    if not sender.author.is_remote or not sender.author.host:
        return


    # determine the type of the inbox item
    inbox_type = sender.inbox_type
    author = sender.author
    obj = sender.content_object
    req = get_request_class_from_host(author.host)

    if inbox_type == Inbox.InboxType.POST:
        req.send_post(obj, author)
    elif inbox_type == Inbox.InboxType.COMMENT:
        req.send_comment(obj, author)
    elif inbox_type == Inbox.InboxType.LIKE:
        req.send_post_like(obj, author)
    elif inbox_type == Inbox.InboxType.COMMENTLIKE:
        req.send_comment_like(obj, author)
    elif inbox_type == Inbox.InboxType.FOLLOW:
        req.send_follow(obj, author)

    return