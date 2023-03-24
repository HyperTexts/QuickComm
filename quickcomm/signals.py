
# This class dispatches external inbox items when they are added to the inbox.
# It uses the signal system to do this, as we cannot properly import the
# model serializers in the model classes.



def export_http_request_on_inbox_save(sender):

    # import here to avoid circular imports
    from quickcomm.external_host_requests import THTHQCRequest
    from quickcomm.external_host_deserializers import Deserializers, InboxSerializers

    from quickcomm.models import Inbox

    print("Inbox item added, sending to external host...")

    # skip if the author is not external
    if not sender.author.is_remote or not sender.author.host:
        return


    # determine the type of the inbox item
    inbox_type = sender.inbox_type
    author = sender.author
    obj = sender.content_object

    if inbox_type == Inbox.InboxType.POST:
        THTHQCRequest(author.host, Deserializers, InboxSerializers).send_post(obj, author)

    return