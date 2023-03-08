

# This file deals with desearializing data from other servers. All of the
# requests will have their data "cached" in our database, so we can just
# access that data instead of making a request to the other server. The calls
# to other servers can then be made independently of our internal calls.

# TODO make sure that our API only return local hosts

from quickcomm.models import Author, Host


def deserialize_author(item, host=None):
    """Deserialize an author from a dictionary."""

    # get host from item
    # FIXME fix for trailing slashes
    host_url = item["host"]

    # check if host exists
    if host is None:
        host = Host.objects.get(url=item["host"])
        if host is None:
            raise Exception(f"Host {host_url} does not exist.")

    # strip id of slashes
    # TODO should we store the ID or the url?
    # id = item["id"].split("/")[-1]

    # check if author exists
    external_url = item["url"]
    author = Author.objects.get(external_url=external_url)
    if author is not None:
        # update author with new data
        author.display_name = item["displayName"]
        author.github = item.get("github", None)
        author.profile_image = item.get("profileImage", None)
        return author

    return Author(
        external_url=item["url"],
        host=host,
        display_name=item["displayName"],
        github=item.get("github", None),
        profile_image=item.get("profileImage", None),
    )