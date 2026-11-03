"""Small, read-only Hygraph pagination example. Python standard library only."""

import json
import urllib.request

ENDPOINT = (
    "https://api-us-east-1-shared-usea1-02.hygraph.com/"
    "v2/cluh3nib3000008jk3ippd87t/master"
)
QUERY = """query AgentSample($first: Int!, $after: String) {
  moviesConnection(first: $first, after: $after, orderBy: id_ASC) {
    edges { cursor node { id } }
    pageInfo { hasNextPage endCursor }
  }
}"""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def fetch_page(first, after):
    """Query only the public movie demo linked in Hygraph's own tutorial."""
    payload = json.dumps({"query": QUERY, "variables": {"first": first, "after": after}})
    request = urllib.request.Request(
        ENDPOINT,
        data=payload.encode(),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    with urllib.request.build_opener(NoRedirect).open(request, timeout=15) as response:
        raw = response.read(65_537)
        if len(raw) > 65_536:
            raise ValueError("Response exceeded the sample's size limit")
        return json.loads(raw)


def collect(fetch, *, page_size=2, max_pages=2):
    """Return an explicitly partial result when the request budget runs out.

    This demonstration starts a fresh traversal. It does not implement durable
    checkpoint storage, retries, authentication, or a consistent snapshot.
    """
    if type(page_size) is not int or not 1 <= page_size <= 100:
        raise ValueError("page_size must be an integer between 1 and 100")
    if type(max_pages) is not int or max_pages < 1:
        raise ValueError("max_pages must be a positive integer")
    ids, seen_ids, seen_cursors = [], set(), set()
    after = None
    for requests in range(1, max_pages + 1):
        envelope = fetch(page_size, after)
        if not isinstance(envelope, dict) or envelope.get("errors"):
            raise ValueError("GraphQL errors: do not treat partial data as a successful export")
        try:
            connection = envelope["data"]["moviesConnection"]
            edges = connection["edges"]
            info = connection["pageInfo"]
            more = info["hasNextPage"]
            end = info["endCursor"]
        except (KeyError, TypeError) as exc:
            raise ValueError("Missing connection or pagination fields") from exc
        if not isinstance(edges, list) or len(edges) > page_size or type(more) is not bool:
            raise ValueError("Unexpected page shape")
        for edge in edges:
            try:
                identifier = edge["node"]["id"]
            except (KeyError, TypeError) as exc:
                raise ValueError("Missing movie id") from exc
            if not isinstance(identifier, str) or not identifier or identifier in seen_ids:
                raise ValueError("Missing or duplicate movie id")
            seen_ids.add(identifier)
            ids.append(identifier)
        if not more:
            return {"ids": ids, "complete": True, "requests": requests, "resume_after": None}
        if not edges or not isinstance(end, str) or not end or end in seen_cursors:
            raise ValueError("Next page reported without an advancing cursor")
        seen_cursors.add(end)
        after = end
    return {"ids": ids, "complete": False, "requests": max_pages, "resume_after": after}


if __name__ == "__main__":
    print(json.dumps(collect(fetch_page), indent=2))
