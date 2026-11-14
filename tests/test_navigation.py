"""One Science Record Player navigation and brand on every public page (#54).

Static checks on the source pages and the built site. The browser behaviour (keyboard,
320px, deep links, sample route) is covered by web/navigation.browser.test.mjs.
"""
import importlib.util
import json
import re
from html.parser import HTMLParser
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("build_site", ROOT / "scripts" / "build_site.py")
build_site = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_site)

MENU = [("/", "Explore"), ("/network/", "My Network"), ("/group/", "Public Group View"), ("/docs/", "How it works"), ("/feedback/", "Feedback")]
PAGES = {"index.html": "/", "network/index.html": "/network/", "group/index.html": "/group/", "feedback/index.html": "/feedback/", "team/index.html": None}


class Links(HTMLParser):
    """Collects every link, and the links and labels of the main menu."""

    def __init__(self):
        super().__init__()
        self.links, self.menu, self.current = [], [], []
        self._depth = 0
        self._link = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "nav" and attrs.get("aria-label") == "Main":
            self._depth = 1
        elif tag == "nav" and self._depth:
            self._depth += 1
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])
            if self._depth:
                self._link = [attrs["href"], ""]
                if attrs.get("aria-current") == "page":
                    self.current.append(attrs["href"])

    def handle_endtag(self, tag):
        if tag == "nav" and self._depth:
            self._depth -= 1
        if tag == "a" and self._link:
            self.menu.append((self._link[0], self._link[1]))
            self._link = None

    def handle_data(self, data):
        if self._link is not None and not self._link[1]:
            self._link[1] = data.strip()


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    out = tmp_path_factory.mktemp("nav") / "site"
    build_site.build(out, client_id="")
    return out


def parse(path: Path) -> Links:
    links = Links()
    links.feed(path.read_text(encoding="utf-8"))
    return links


@pytest.mark.parametrize("page", PAGES)
def test_every_page_has_the_same_menu_with_the_current_page_marked(site, page):
    links = parse(site / page)
    assert links.menu == MENU, page
    assert links.current == ([PAGES[page]] if PAGES[page] else []), page


@pytest.mark.parametrize("page", PAGES)
def test_cloud_teams_are_not_offered_from_any_menu(site, page):
    # Production activation of private cloud Teams is not verified (#22): no menu entry.
    assert not [href for href, _ in parse(site / page).menu if href.startswith("/team")]
    network = parse(site / "network" / "index.html")
    assert not [href for href in network.links if href.startswith("/team")]


def test_teams_page_is_labelled_experimental_and_unavailable(site):
    html = (site / "team" / "index.html").read_text(encoding="utf-8")
    assert "Teams (experimental, not available)" in html
    assert "Experimental: private cloud Teams are not available yet." in html
    assert 'href="/network/#groups"' in html and 'href="/group/"' in html


def test_internal_links_resolve_in_the_built_site(site):
    for page in PAGES:
        for href in parse(site / page).links:
            if not href.startswith("/") or href.startswith("//"):
                continue
            path = href.split("#")[0].split("?")[0]
            if path == "/docs/":
                continue  # bundled by .github/workflows/deploy-hosting.yml, checked below
            target = site / path.lstrip("/")
            assert target.is_file() or (target / "index.html").is_file(), f"{page} links to missing {href}"
    deploy = (ROOT / ".github" / "workflows" / "deploy-hosting.yml").read_text(encoding="utf-8")
    assert "cp -a docs/_build/html/. site/docs/" in deploy


def test_network_page_carries_the_parent_brand_not_a_separate_one(site):
    brand = build_site.load_brand()
    source = (ROOT / "web" / "network" / "index.html").read_text(encoding="utf-8")
    # The local `srp network` server serves this file without the build's __BRAND_ tokens,
    # so the name is written out; it must stay in step with config/brand.json.
    assert f'<meta name="application-name" content="{brand["name"]}">' in source
    assert f"<strong>{brand['name']}</strong>" in source and f"<title>My Network · {brand['name']}</title>" in source
    for old in ("in good company", "THE RESEARCH COMMONS", "Research network"):
        assert old not in source
    hosted = (site / "network" / "index.html").read_text(encoding="utf-8")
    assert "PILOT" not in hosted and "MY NETWORK · IN THIS BROWSER" in hosted
    assert 'aria-labelledby="network-sections-label"' in hosted
    assert '<a href="/">← Back to Explore</a>' in hosted


def test_menu_hints_tell_local_groups_from_public_group_view():
    for page in ("index.html", "group.html", "feedback.html", "team.html"):
        html = (ROOT / "web" / "playground" / page).read_text(encoding="utf-8")
        assert '<span class="nav-label">My Network</span><span class="nav-hint">stored in this browser</span>' in html, page
        assert '<span class="nav-label">Public Group View</span><span class="nav-hint">shareable link</span>' in html, page


def test_docs_share_the_menu():
    conf = (ROOT / "docs" / "source" / "conf.py").read_text(encoding="utf-8")
    labels = re.findall(r'<a href="([^"]+)"[^>]*>([^<]+)</a>', conf)
    assert labels == MENU


def test_storage_and_backup_identifiers_are_unchanged():
    # Renaming these would orphan existing browser workspaces and backups (no implicit migration).
    from science_record_player import network_store
    assert network_store.WORKSPACE_FORMAT == "orcid-playground-workspace"
    assert network_store.GROUP_PACKAGE_FORMAT == "orcid-playground-team-group"
    web = "\n".join(p.read_text(encoding="utf-8") for p in (ROOT / "web").rglob("*.js"))
    for key in ("'orcid-playground-workspace'", "'orcid-playground-team-pack'", "'orcid-playground-last-visit'",
                "'orcid-playground-signin'", "'orcid-playground-autosave'", "'orcid-playground-cloud'", "'orcid-playground-my-check'"):
        assert key in web, key


def test_ci_runs_the_browser_navigation_tests():
    ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "web/navigation.browser.test.mjs" in ci and "SRP_REQUIRE_BROWSER: \"1\"" in ci
    assert json.loads((ROOT / "demo" / "package.json").read_text(encoding="utf-8"))["dependencies"]["playwright"]
