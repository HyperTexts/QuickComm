


# This file deals with calling other API endpoints and returning the results in
# a dictionary format. This file also deals with the weirdness of pagination
# and caching external requests.

import requests_cache

# This caches the requests for 5 minutes, but this can be changed
session = requests_cache.CachedSession('external_cache', expire_after=300)

def get_authors(url):
    """Get all author details from a host. This function will raise an exception
    if the request fails."""

    # clean up the URL
    if url[-1] == '/':
        url = url[:-1]

    # get the authors
    empty = False
    authors = []
    page = 1
    while not empty:

        # call api
        response = session.get(f'{url}/authors', params={'page': page, 'size': 5})

        # check response code
        if response.status_code != 200:
            raise Exception(f'Error getting authors from {url}: {response.status_code}')

        # check response type
        assert(response.json()["type"] == "authors")

        # loop though authors
        curr_authors = response.json()["items"]
        if len(curr_authors) == 0:
            empty = True
            break
        authors += curr_authors
        page += 1

    return authors

