import itertools
from datetime import timezone
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import requests
from dateutil.parser import parse

import queries


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
        links = parse_links(response.headers.get("Link", ""))
        url = links.get("next")
    return items


def get_org(name, **kwargs):
    return github_api_request(f"https://api.github.com/orgs/{name}", **kwargs).json()


def github_api_request(url, access_token, skip_ssl_verification=False, **kw):
    url = update_query_params(url, per_page=100)
    return requests.get(
        url,
        verify=(not skip_ssl_verification),
        headers={"Authorization": f"token {access_token}"},
    )
def graphql_client(access_token):
    def graphql_query(q):
        resp = requests.post(
            "https://api.github.com/graphql",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"query": q}
        )
        resp.raise_for_status()
        return resp.json()
    return graphql_query

def update_query_params(url, **kwargs):
    """
    Updates a URLs query string, inserting or replacing specified parameters.

    >>> update_query_params('http://example.com', foo=1)
    'http://example.com?foo=1'
    >>> update_query_params('http://example.com?foo=1', foo=2)
    'http://example.com?foo=2'
    >>> update_query_params('http://example.com?foo=1&foo=2', bar=3)
    'http://example.com?foo=1&foo=2&bar=3'
    """
    QUERY = 4
    url_parts = list(urlparse(url))
    query_params = parse_qs(url_parts[QUERY])
    query_params.update(kwargs)
    url_parts[QUERY] = urlencode(query_params, doseq=True)
    return urlunparse(url_parts)


def parse_links(s):
    """
    Parse URLs from Link header

    >>> links = parse_links(
    ...     '<https://api.github.com/repos?page=2>; rel="next", '
    ...     '<https://api.github.com/repos?page=5>; rel="last"')
    >>> list(links.keys())
    ['next', 'last']
    >>> links['next']
    'https://api.github.com/repos?page=2'
    >>> links['last']
    'https://api.github.com/repos?page=5'
    """
    links = {}
    for link in s.split(","):
        url, rel = link.strip().split(";")
        url = url.strip(" <>")
        rel = rel.strip().replace("rel=", "").strip('"')
        links[rel] = url
    return links


def pushed_at(r):
    return int(parse(r["pushedAt"]).replace(tzinfo=timezone.utc).timestamp())


def get_all_repos(source):
    client = graphql_client(source["access_token"])
    all_repos = []
    repos = client(queries.repos(source["name"]))
    all_repos.append(repos)
    while repos["data"]["organization"]["repositories"]["pageInfo"][
        "hasNextPage"]:
        cursor = f'"{repos["data"]["organization"]["repositories"]["pageInfo"]["endCursor"]}"'
        repos = client(queries.repos(source["name"], after=cursor))
        all_repos.append(repos)
    repo_list = [
        y["node"]
        for y in itertools.chain.from_iterable(
            [x["data"]["organization"]["repositories"]["edges"] for x in
             all_repos]
        )
    ]
    return repo_list
