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
                         "Dog. Man’s Best Friend.")
        self.assertIn("Colorado Springs, Fountain, Pueblo", text(self.html))
        self.assertRegex(self.html, r'<a [^>]*href="/faq/location/"[^>]*>Details</a>')

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
        for fact in ["$30 deposit", "$100", "Friday", "Saturday", "Colorado Springs"]:
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


class Phone(unittest.TestCase):
    def test_phone_on_book_contact_and_home(self):
        for path in ["/book/", "/contact/", "/"]:
            html = page(path)
            self.assertIn('href="tel:+14065335127"', unescape(html), path)
            self.assertIn("406-533-5127", text(html), path)

    def test_contact_page_is_not_placeholder(self):
        t = text(page("/contact/"))
        self.assertNotIn("aren’t live yet", t)
        self.assertIn("training@k9-communication.com", t)


INVITE = "https://discord.gg/AvS8RRSgJ"


class ClientCommunity(unittest.TestCase):
    def test_invite_page_has_link_and_qr(self):
        html = page("/join-the-pack/")
        self.assertIn(f'href="{INVITE}"', html)
        self.assertRegex(html, r'<img [^>]*src="/images/discord-invite-qr\.png"')
        self.assertTrue(os.path.exists(os.path.join(PUBLIC, "images", "discord-invite-qr.png")))
        self.assertIn('<meta name="robots" content="noindex', html)

    def test_invite_page_is_unlisted(self):
        with open(os.path.join(PUBLIC, "sitemap.xml"), encoding="utf-8") as f:
            self.assertNotIn("join-the-pack", f.read())
        with open(os.path.join(PUBLIC, "index.json"), encoding="utf-8") as f:
            index = f.read()
        self.assertNotIn("join-the-pack", index)
        self.assertNotIn(INVITE, index)
        self.assertNotIn("join-the-pack", page("/"))

    def test_invite_link_only_on_invite_page(self):
        for root, _, files in os.walk(PUBLIC):
            for name in files:
                if name.endswith((".html", ".json", ".xml")):
                    rel = os.path.relpath(os.path.join(root, name), PUBLIC)
                    if rel.startswith("join-the-pack"):
                        continue
                    with open(os.path.join(root, name), encoding="utf-8") as f:
                        self.assertNotIn(INVITE, f.read(), rel)

    def test_book_page_mentions_community_without_link(self):
        t = text(page("/book/"))
        self.assertIn("Discord community", t)


class HowDogsLearn(unittest.TestCase):
    def test_page_exists_with_conditioning_copy(self):
        t = text(page("/faq/how-dogs-learn/"))
        self.assertIn("How do dogs learn?", t)
        self.assertIn("Classical conditioning", t)
        self.assertIn("Operant conditioning", t)


class Payments(unittest.TestCase):
    PAY_LABELS = ["Pay $30 deposit", "Pay $70 session remainder",
                  "Pay for 1-10 sessions", "Buy a pack after your deposit"]

    def live_page(self, path):
        out = tempfile.mkdtemp(prefix="k9-site-live-")
        self.addCleanup(shutil.rmtree, out, ignore_errors=True)
        subprocess.run(["hugo", "--quiet", "-d", out], cwd=ROOT, check=True,
                       env={**os.environ, "HUGO_PARAMS_PAYMENTSLIVE": "true"})
        with open(os.path.join(out, path.strip("/"), "index.html"), encoding="utf-8") as f:
            return f.read()

    def test_hidden_while_payments_are_off(self):
        for path in ["/book/", "/pay/", "/"]:
            self.assertNotIn("stripe.com", page(path), path)
        self.assertNotIn('href="/pay/"', page("/"))
        self.assertIn("isn’t open yet", text(page("/pay/")))

    def test_pay_page_when_payments_are_on(self):
        html = self.live_page("/pay/")
        for label in self.PAY_LABELS:
            self.assertIn(label, text(html))
        self.assertEqual(len(set(re.findall(r'href="(https://buy\.stripe\.com/[^"]+)"', html))), 4)
        self.assertIn('href="/pay/"', html)

    def test_book_page_when_payments_are_on(self):
        html = self.live_page("/book/")
        self.assertIn('href="/pay/"', html)
        self.assertNotRegex(text(html[html.find("k9-hero"):html.find("<footer")]), r"\$\d")
        self.assertNotIn("calendar.proton.me", html)


RESUME_VIDEOS = ["nDTvE199qhM", "6xY6tbOXQx8", "ytUBuQI52XQ", "V2qxq1B5FCA",
                 "SnMAGTHxG2Y", "cFSE0V6iDTQ", "1piLf035sk8"]


class DogsResume(unittest.TestCase):
    RECORD = "/training-records/dogs-of-k9-communication/"

    def test_record_embeds_every_video_and_links_its_services(self):
        html = page(self.RECORD)
        for vid in RESUME_VIDEOS:
            self.assertIn(vid, html, vid)
        for service in ["food-and-play-training", "escape-and-avoidance-training",
                        "e-collar-bootcamp", "training-with-kids", "group-lessons"]:
            self.assertIn(f'href="/services/{service}/', html, service)

    def test_training_with_kids_service(self):
        t = text(page("/services/training-with-kids/"))
        self.assertIn("Training with Kids", t)
        titles = re.findall(r"<strong>(.*?)</strong>", page("/services/"))
        i = titles.index("Training with Kids")
        self.assertEqual(titles[i - 1:i + 2],
                         ["Escape and Avoidance Training", "Training with Kids", "Behavior Modification"])

    def test_home_carousel(self):
        home = page("/")
        start = home.find('id="resume"')
        self.assertNotEqual(start, -1)
        self.assertLess(home.find('id="how-it-works"'), start)
        self.assertLess(start, home.find('id="services"'))
        resume = home[start:home.find('id="services"')]
        self.assertEqual(text(re.search(r"<h2\b[^>]*>(.*?)</h2>", resume, re.S).group(1)).strip(),
                         "My dogs are my resume")
        # Kids handling big dogs leads; the rest follow the record's order.
        rail = re.findall(r'<a href="https://www\.youtube\.com/watch\?v=([\w-]+)"', resume)
        self.assertEqual(rail, RESUME_VIDEOS[-1:] + RESUME_VIDEOS[:-1])
        self.assertIn(f'href="{self.RECORD}', resume)
        # Players load on click, so the home page ships no YouTube iframes.
        self.assertNotIn("<iframe", resume)


class Plan(unittest.TestCase):
    ANCHOR = "/services/in-home-consult/#how-we-make-your-plan"

    def test_consult_page_explains_the_plan(self):
        html = page("/services/in-home-consult/")
        self.assertIn('class="k9-thr"', html)
        steps = html[html.find('class="k9-steps"'):html.find('id="what-a-layered-plan-looks-like"')]
        self.assertEqual(len(re.findall(r"<li>", steps)), 5)
        t = text(html)
        self.assertLess(t.find("How we make your plan"), t.find("The deposit"))

    def test_home_plan_step_links_to_it(self):
        self.assertRegex(page("/"), re.escape(f'href="{self.ANCHOR}"') + r'>\s*<span class="k9-num">2</span>')

    def test_foundation_services_say_why(self):
        ff = text(page("/services/food-and-play-training/"))
        self.assertLess(ff.find("Why we use it"), ff.find("Where we use it"))
        self.assertLess(ff.find("Where we use it"), ff.find("Reward markers"))
        self.assertIn(f'href="{self.ANCHOR}"', page("/services/food-and-play-training/"))
        ea = text(page("/services/escape-and-avoidance-training/"))
        self.assertLess(ea.find("Why we use it"), ea.find("How I use pressure"))
        self.assertLess(ea.find("Why it becomes rewarding"), ea.find("Why we layer food and play back in"))
        self.assertIn("Premack principle", ea)


class Pricing(unittest.TestCase):
    def test_equipment_is_not_required(self):
        t = text(page("/faq/pricing/"))
        self.assertIn("None of this is required", t)
        self.assertNotIn("I require", t)
        self.assertNotIn("what equipment do I need", t)
        for path in ["/faq/first-session/", "/services/escape-and-avoidance-training/"]:
            self.assertNotRegex(text(page(path)), r"equipment you’ll need|need some equipment", path)

    def test_no_mileage_rate_in_faq(self):
        for root, _, files in os.walk(os.path.join(PUBLIC, "faq")):
            for name in files:
                with open(os.path.join(root, name), encoding="utf-8") as f:
                    self.assertNotRegex(f.read().lower(), r"mileage|0\.70", os.path.join(root, name))


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
