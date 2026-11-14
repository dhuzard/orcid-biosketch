"""The homepage's two equally weighted paths (issue #53): copy, link targets and layout."""

import importlib.util
import os
import re
import shutil
import subprocess
import threading
from functools import partial
from html.parser import HTMLParser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("build_site", ROOT / "scripts" / "build_site.py")
build_site = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_site)


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    out = tmp_path_factory.mktemp("homepage") / "site"
    build_site.build(out, client_id="")
    return out


@pytest.fixture(scope="module")
def hero(site):
    html = (site / "index.html").read_text(encoding="utf-8")
    return html[html.index('<section class="hero"'):html.index('<section id="me"')]


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.headings, self._heading = [], [], None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a":
            self.links.append(attrs)
        if tag in {"h1", "h2", "h3"}:
            self._heading = [tag, attrs.get("id"), ""]

    def handle_data(self, data):
        if self._heading:
            self._heading[2] += data

    def handle_endtag(self, tag):
        if self._heading and tag == self._heading[0]:
            self.headings.append(tuple(self._heading))
            self._heading = None


def parse(html):
    parser = Links()
    parser.feed(html)
    return parser


def test_headline_and_both_tracks_have_accessible_headings(hero):
    headings = parse(hero).headings
    assert headings == [
        ("h1", "hero-title", "Explore your scientific record. Connect your research world."),
        ("h2", "track-explore-title", "Explore & Play"),
        ("h2", "track-connect-title", "Connect & Organize"),
    ]
    assert 'aria-labelledby="track-explore-title"' in hero and 'aria-labelledby="track-connect-title"' in hero
    assert "PUBLISH OR PLAY" in hero  # kept as the secondary brand line


def test_plain_language_notes(hero):
    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", hero))
    assert "No sign-in is needed to explore public ORCID records." in text
    assert "A public ORCID record is a set of assertions" in text
    assert "none of them verifies identity, authorship or affiliations" in text
    assert "stay in this browser by default; nothing is uploaded" in text
    assert "Sample data is added only after you confirm" in text and "labelled “Demo”" in text
    for feature in ("profile", "trading card", "publication heatmap", "Wrapped", "record check", "citation exports"):
        assert feature in text, feature
    for feature in ("contacts", "conference notes", "follow-ups", "working groups", "team pack"):
        assert feature in text, feature


def test_cta_targets(hero):
    links = parse(hero).links
    by_cta = {a["data-track-cta"]: a["href"] for a in links if "data-track-cta" in a}
    assert by_cta == {"connect": "/network/#contacts", "sample": "/network/?sample=1#groups"}
    assert [a["href"] for a in links if a.get("class") == "path"] == ["#track-explore", "#track-connect"]
    assert {a["href"] for a in links} == {"#track-explore", "#track-connect", "/network/#contacts", "/network/?sample=1#groups", "/feedback/"}
    # Track A's first actions are the Studio lookup and the stored, offline profile on this page.
    assert '<form id="lookup"' in hero and "data-sample>" in hero and 'data-orcid="0000-0002-1825-0097"' in hero
    assert hero.index('id="track-explore"') < hero.index('id="lookup"') < hero.index('id="track-connect"')


def test_link_targets_exist_in_the_built_site(site):
    assert (site / "network" / "index.html").is_file() and (site / "feedback" / "index.html").is_file()
    assert (site / "generated" / "biosketch.json").is_file()  # the stored demo profile
    bridge = (site / "network-bridge.js").read_text(encoding="utf-8")
    # ?sample=1 asks first; it never fills the workspace by itself.
    assert "params.has('sample')" in bridge and "confirm(" in bridge
    assert "groups" in (ROOT / "web" / "network" / "app.js").read_text(encoding="utf-8")


def test_no_unverified_cloud_feature_or_unpublished_demo_is_offered(hero):
    lowered = hero.lower()
    for claim in ("cloud", "sync", "sign in", "teams", "/team/", "invite", "video", "youtube"):
        assert claim not in lowered, claim


def test_studio_script_hooks_are_still_in_the_hero(hero):
    # studio.js binds these; the redesign must not break them.
    for hook in ('id="lookup"', 'id="orcid"', 'id="status"', 'id="mine"', "data-sample", "data-orcid="):
        assert hook in hero, hook
    assert 'role="status" aria-live="polite"' in hero


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def _playwright_available():
    node = shutil.which("node")
    if not node:
        return None
    probe = subprocess.run([node, "-e", "require('playwright')"], capture_output=True, cwd=ROOT)
    return node if probe.returncode == 0 else None


def test_homepage_in_a_browser(site):
    """Layouts at 320/375px and desktop, keyboard order, CTA targets, consent and loading/empty states."""
    required = os.environ.get("SRP_REQUIRE_BROWSER") == "1"  # CI: a missing browser is a failure
    node = _playwright_available()
    if not node:
        assert not required, "Node.js with Playwright is required (SRP_REQUIRE_BROWSER=1)"
        pytest.skip("Node.js with Playwright is not available")
    handler = partial(QuietHandler, directory=str(site))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        result = subprocess.run(
            [node, str(ROOT / "tests" / "e2e" / "homepage.e2e.cjs"), f"http://127.0.0.1:{server.server_address[1]}"],
            capture_output=True, text=True, timeout=300, cwd=ROOT,
        )
    finally:
        server.shutdown()
    if result.returncode == 77:
        assert not required, f"No usable Chromium: {result.stderr.strip()[:200]}"
        pytest.skip(f"No usable Chromium: {result.stderr.strip()[:200]}")
    assert result.returncode == 0, result.stdout + result.stderr
