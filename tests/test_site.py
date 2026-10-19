"""Builds the site with Hugo and checks the rendered output, the way a visitor sees it.

Run: python3 -m unittest discover tests
"""
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from html import unescape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def setUpModule():
    global PUBLIC
    PUBLIC = tempfile.mkdtemp(prefix="k9-site-")
    subprocess.run(["hugo", "--quiet", "-d", PUBLIC], cwd=ROOT, check=True)


def tearDownModule():
    shutil.rmtree(PUBLIC, ignore_errors=True)


def page(path):
    with open(os.path.join(PUBLIC, path.strip("/"), "index.html"), encoding="utf-8") as f:
        return f.read()


def text(html):
    html = re.sub(r"<(script|style)\b.*?</\1>", " ", html, flags=re.S)
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", html)))


class HomePage(unittest.TestCase):
    def setUp(self):
        self.html = page("/")

    def test_headline_and_area_line(self):
        h1 = re.search(r"<h1\b[^>]*>(.*?)</h1>", self.html, re.S)
        self.assertIsNotNone(h1)
        self.assertEqual(text(h1.group(1)).strip(),
                         "In-home dog training through classical and operant conditioning")
        self.assertIn("El Paso County, Colorado, and surrounding areas", text(self.html))
        self.assertRegex(self.html, r'<a [^>]*href="/faq/location/"[^>]*>surrounding areas</a>')

    def test_sections_in_order(self):
        ids = ["hero", "how-it-works", "services", "pricing", "how-i-train", "book"]
        positions = [self.html.find(f'id="{i}"') for i in ids]
        self.assertNotIn(-1, positions, dict(zip(ids, positions)))
        self.assertEqual(positions, sorted(positions))

    def test_chat_is_first_and_only_once(self):
        forms = [m.start() for m in re.finditer(r'<form\b[^>]*class="[^"]*k9-chat', self.html)]
        self.assertEqual(len(forms), 1)
        self.assertLess(forms[0], self.html.find('id="how-it-works"'))

    def test_suggested_questions(self):
        suggestions = [text(s).strip() for s in
                       re.findall(r'<button\b[^>]*class="[^"]*k9-suggest[^"]*"[^>]*>(.*?)</button>', self.html, re.S)]
        self.assertEqual(suggestions, [
            "How much does training cost?",
            "What does a training plan look like?",
        ])

    def test_no_logo_in_hero(self):
        hero = self.html[self.html.find('id="hero"'):self.html.find('id="how-it-works"')]
        self.assertNotIn("<img", hero)

    def test_book_a_consult_in_hero(self):
        hero = self.html[self.html.find('id="hero"'):self.html.find('id="how-it-works"')]
        self.assertIn("Book a consult", text(hero))

    def test_pricing_and_area_facts(self):
        pricing = text(self.html[self.html.find('id="pricing"'):self.html.find('id="how-i-train"')])
        for fact in ["$30 deposit", "$100", "Friday", "Saturday", "mileage fee"]:
            self.assertIn(fact, pricing)

    def test_no_placeholder_testimonial(self):
        self.assertNotIn('id="testimonial"', self.html)
        self.assertNotIn("Placeholder", text(self.html))

    def test_traditional_defined_at_first_mention(self):
        t = text(self.html).lower()
        first = t.find("traditional")
        self.assertNotEqual(first, -1)
        self.assertIn("escape and avoidance training", t[max(0, first - 80):first + 80])

    def test_links_to_how_dogs_learn(self):
        self.assertIn('href="/faq/how-dogs-learn/"', self.html)


class HowDogsLearn(unittest.TestCase):
    def test_page_exists_with_conditioning_copy(self):
        t = text(page("/faq/how-dogs-learn/"))
        self.assertIn("How do dogs learn?", t)
        self.assertIn("Classical conditioning", t)
        self.assertIn("Operant conditioning", t)


class Links(unittest.TestCase):
    def test_internal_links_and_anchors_resolve(self):
        broken = set()
        for root, _, files in os.walk(PUBLIC):
            for name in files:
                if not name.endswith(".html"):
                    continue
                with open(os.path.join(root, name), encoding="utf-8") as f:
                    for href in re.findall(r'href="(/[^"]*)"', f.read()):
                        path, _, frag = href.partition("#")
                        target = os.path.join(PUBLIC, path.lstrip("/"))
                        if os.path.isdir(target):
                            target = os.path.join(target, "index.html")
                        if not os.path.exists(target):
                            broken.add(href)
                        elif frag and target.endswith(".html"):
                            with open(target, encoding="utf-8") as t:
                                if f'id="{frag}"' not in t.read():
                                    broken.add(href)
        self.assertEqual(broken, set())


if __name__ == "__main__":
    unittest.main()
