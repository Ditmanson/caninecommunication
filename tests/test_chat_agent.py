"""Unit tests for the chat agent Lambda, with AWS and the network stubbed out.

Run: python3 -m unittest discover tests
"""
import importlib.util
import io
import json
import os
import sys
import unittest
import urllib.request  # before load_handler: patch.dict unloads whatever is first imported inside it
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SITE = [{"title": f"Recall page {i}", "url": f"https://k9-communication.com/{i}/", "tags": [], "summary": "recall"}
        for i in range(8)]
BLOG = [{"title": "Recall games", "url": "https://griz.sh/posts/recall/", "tags": ["recall"], "summary": "games",
         "body": "long " * 2000, "card": "<article>markup</article>"}]


def load_handler():
    """Imports handler.py without boto3 installed or AWS reachable."""
    stubs = {name: mock.MagicMock() for name in ("boto3", "botocore", "botocore.config", "botocore.exceptions")}
    path = os.path.join(ROOT, "lambda/chat-agent/handler.py")
    spec = importlib.util.spec_from_file_location("chat_agent_handler", path)
    module = importlib.util.module_from_spec(spec)
    with mock.patch.dict(sys.modules, stubs):
        spec.loader.exec_module(module)
    return module


def fake_web(pages):
    def urlopen(url, timeout=None):
        if isinstance(pages[url], Exception):
            raise pages[url]
        return io.BytesIO(json.dumps(pages[url]).encode())
    return mock.patch.object(urllib.request, "urlopen", side_effect=urlopen)


class BlogIndex(unittest.TestCase):
    def setUp(self):
        self.agent = load_handler()
        self.site_url = "https://k9-communication.com/index.json"
        self.blog_url = "https://griz.sh/index.json"

    def test_prompt_lists_blog_posts_without_bodies(self):
        with fake_web({self.site_url: SITE, self.blog_url: BLOG}):
            prompt = self.agent._build_system_prompt()
        self.assertIn("https://griz.sh/posts/recall/", prompt)
        self.assertNotIn("long long", prompt)
        self.assertNotIn("<article>", prompt)

    def test_search_finds_blog_even_when_site_fills_its_limit(self):
        with fake_web({self.site_url: SITE, self.blog_url: BLOG}):
            results = self.agent._execute_tool("search_site_content", {"query": "recall"})
        urls = [r["url"] for r in results]
        self.assertIn("https://griz.sh/posts/recall/", urls)
        self.assertEqual(len(urls), 6)
        self.assertNotIn("long long", json.dumps(results))

    def test_survives_blog_being_down(self):
        with fake_web({self.site_url: SITE, self.blog_url: OSError("down")}):
            self.assertIn("https://k9-communication.com/1/", self.agent._build_system_prompt())
            self.assertEqual(len(self.agent._execute_tool("search_site_content", {"query": "recall"})), 5)

    def test_survives_blog_returning_the_wrong_shape(self):
        with fake_web({self.site_url: SITE, self.blog_url: {"oops": True}}):
            self.assertIn("https://k9-communication.com/1/", self.agent._build_system_prompt())


class Spend(unittest.TestCase):
    def setUp(self):
        self.agent = load_handler()

    def test_cached_tokens_are_billed(self):
        # Bedrock Haiku 4.5 through a us. profile, per 1M: input 1.10, output 5.50, cache write 1.375, read 0.11
        usage = {"input_tokens": 1000, "output_tokens": 100,
                 "cache_creation_input_tokens": 4000, "cache_read_input_tokens": 8000}
        self.assertEqual(self.agent._usage_cost_microdollars(usage), 1100 + 550 + 5500 + 880)

    def test_reservation_covers_a_worst_case_question(self):
        pages = {"https://k9-communication.com/index.json": SITE, "https://griz.sh/index.json": BLOG}
        with fake_web(pages):
            self.agent._get_content_index("https://k9-communication.com/index.json")
            prompt_tokens = len(self.agent._build_system_prompt()) // 4
            reserved = self.agent._max_request_cost_microdollars()
        calls = self.agent.MAX_TOOL_ITERATIONS
        uncached_floor = calls * (prompt_tokens * 1.375 + self.agent.MAX_OUTPUT_TOKENS * 5.5)
        self.assertGreater(reserved, uncached_floor)
