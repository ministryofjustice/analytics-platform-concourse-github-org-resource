from datetime import timezone
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from dateutil.parser import parse
import requests


def get_all(url, **kwargs):
    """
    Get a list of all items across all pages of a Github API resource. Parses
    the `Link` response header to find subsequent pages and recurses until no
    `next` URL is given.
    """
    items = []
    while url:
        response = github_api_request(url, **kwargs)
        items += response.json()
        links = parse_links(response.headers.get('Link', ''))
        url = links.get('next')
    return items


def get_org(name, **kwargs):
    return github_api_request(
        f'https://api.github.com/orgs/{name}', **kwargs).json()


def github_api_request(url, access_token, skip_ssl_verification=False, **kw):
    url = update_query_params(url, per_page=100)
    return requests.get(url, verify=(not skip_ssl_verification), headers={
        'Authorization': f'token {access_token}'}
    )


def update_query_params(url, **kwargs):
    """
    Updates a URLs query string, inserting or replacing specified parameters.

    >>> update_query_params('http://example.com', foo=1)
    'http://example.com?foo=1'
    >>> update_query_params('http://example.com?foo=1', foo=2)
    'http://example.com?foo=2'
    """
    QUERY = 4
    url_parts = list(urlparse(url))
    query_params = parse_qs(url_parts[QUERY])
    query_params.update(kwargs)
    url_parts[QUERY] = urlencode(query_params)
    return urlunparse(url_parts)


def parse_links(s):
    """
    Parse URLs from Link header

    >>> parse_links(
    >>>     '<https://api.github.com/resource?page=2; rel="next", '
    >>>     '<https://api.github.com/resource?page=5; rel="last')
    {
        'next': 'https://api.github.com/resource?page=2',
        'last': 'https://api.github.com/resource?page=5'
    }
    """
    links = {}
    for link in s.split(','):
        url, rel = link.strip().split('; ')
        url = url[1:-1]
        rel = rel[5:-1]
        links[rel] = url
    return links


def pushed_at(r):
    return parse(r['pushed_at']).replace(tzinfo=timezone.utc).timestamp()
