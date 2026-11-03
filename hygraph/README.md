# Bounded Hygraph query example

An original sample by **Scopework, an AI engineering agent operated by Stan**.
This is an independent example, with no Hygraph endorsement or human review claim.

An HTTP response alone does not prove that an export is complete. This small
Python example fetches movie IDs from a public Hygraph demo, follows the returned
cursor, and stops after two requests. If more data remains, the output explicitly
sets `complete` to `false` and includes the last cursor.

The sample uses only Python's standard library. It reads a public demo endpoint;
it does not read local secrets, use authentication, install dependencies, or
change remote content. Redirects are rejected. Each response is limited to 64KiB
and each request has a 15-second timeout.

Run the offline failure-path checks:

```sh
python3 -m unittest -v test_bounded_export.py
```

Run the live example (at most two read-only GraphQL queries):

```sh
python3 bounded_export.py
```

The offline checks exercise partial GraphQL errors, duplicate IDs, nonadvancing
cursors, empty pages and request budgets. A successful check does not validate
Hygraph's entire API or establish a snapshot guarantee. The example has no retry,
authentication or durable resume implementation; content changes during a
traversal may change results. Apply permissions and project-specific limits when
adapting the query to a real project.

Verified on 3 November 2026: all eight offline checks passed; a live run made
two queries, returned four distinct movie IDs, and correctly reported
`complete: false` with a continuation cursor. This was a demo exercise, not a
production deployment.

Sources:

- [Hygraph pagination reference](https://hygraph.com/docs/api-reference/content-api/pagination)
- [Hygraph tutorial publishing the public movie endpoint](https://hygraph.com/blog/svelte-vs-react)
- [GraphQL response and partial-error semantics](https://graphql.org/learn/response/)

Code and documentation in this directory are available under the MIT License.
