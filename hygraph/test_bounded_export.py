"""Failure-path checks for the pagination sample. No network requests."""

import unittest

from bounded_export import collect


def page(ids, *, more=False, cursor=None):
    return {"data": {"moviesConnection": {
        "edges": [{"node": {"id": value}} for value in ids],
        "pageInfo": {"hasNextPage": more, "endCursor": cursor},
    }}}


class ExportChecks(unittest.TestCase):
    def test_request_budget_never_claims_finished_export(self):
        calls = []
        def fetch(first, after):
            calls.append((first, after))
            return page(["one"], more=True, cursor="cursor-one")
        result = collect(fetch, max_pages=1)
        self.assertFalse(result["complete"])
        self.assertEqual(result["resume_after"], "cursor-one")
        self.assertEqual(calls, [(2, None)])

    def test_next_request_uses_the_returned_cursor(self):
        calls = []
        def fetch(first, after):
            calls.append(after)
            return page(["one"], more=True, cursor="c1") if after is None else page(["two"])
        result = collect(fetch)
        self.assertTrue(result["complete"])
        self.assertEqual(result["ids"], ["one", "two"])
        self.assertEqual(calls, [None, "c1"])

    def test_empty_terminal_page_is_complete(self):
        self.assertTrue(collect(lambda *args: page([]))["complete"])

    def test_graphql_errors_reject_otherwise_valid_partial_data(self):
        value = page(["one"])
        value["errors"] = [{"message": "Resolver failed"}]
        with self.assertRaises(ValueError):
            collect(lambda *args: value)

    def test_repeated_cursor_stops_before_a_third_request(self):
        replies = iter([page(["one"], more=True, cursor="c1"),
                        page(["two"], more=True, cursor="c1")])
        with self.assertRaises(ValueError):
            collect(lambda *args: next(replies), max_pages=3)

    def test_duplicate_id_across_pages_is_reported(self):
        replies = iter([page(["one"], more=True, cursor="c1"), page(["one"])])
        with self.assertRaises(ValueError):
            collect(lambda *args: next(replies))

    def test_nonterminal_empty_page_is_rejected(self):
        with self.assertRaises(ValueError):
            collect(lambda *args: page([], more=True, cursor="c1"))

    def test_invalid_budgets_make_no_requests(self):
        def forbidden(*args):
            self.fail("Invalid arguments must fail before any network call")
        for kwargs in [{"max_pages": 0}, {"page_size": 101}, {"page_size": True}]:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                collect(forbidden, **kwargs)


if __name__ == "__main__":
    unittest.main()
