

# This file deals with desearializing data from other servers. All of the
# requests will have their data "cached" in our database, so we can just
# access that data instead of making a request to the other server. The calls
# to other servers can then be made independently of our internal calls.

# TODO make sure that our API only return local hosts
# TODO what do we do when we see authors that aren't on any of our servers or a host we know about?


