from __future__ import annotations

import functools
import os
import re
import shutil
import statistics
import subprocess
import threading
from html.parser import HTMLParser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Iterator

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
LIVE_ENABLED = os.environ.get("DOCS_LIVE_TESTS") == "1"


class ScriptParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.scripts: list[tuple[dict[str, str | None], str]] = []
        self._attrs: dict[str, str | None] | None = None
        self._content: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "script":
            self._attrs = dict(attrs)
            self._content = []

    def handle_data(self, data: str) -> None:
        if self._attrs is not None:
            self._content.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._attrs is not None:
            self.scripts.append((self._attrs, "".join(self._content)))
            self._attrs = None


class DocsRequestHandler(SimpleHTTPRequestHandler):
    def log_request(self, code: int | str = "-", size: int | str = "-") -> None:
        if isinstance(code, int) and code >= 400:
            super().log_request(code, size)


def test_site_head_configures_math_before_loading_cdn() -> None:
    parser = ScriptParser()
    parser.feed((DOCS / "_includes" / "head_custom.html").read_text(encoding="utf-8"))
    configs = [
        (index, text) for index, (_, text) in enumerate(parser.scripts)
        if "window.MathJax" in text
    ]
    loaders = [
        (index, attrs) for index, (attrs, _) in enumerate(parser.scripts)
        if "mathjax" in (attrs.get("src") or "").lower()
    ]

    assert len(configs) == len(loaders) == 1
    config_index, config = configs[0]
    loader_index, loader = loaders[0]
    assert config_index < loader_index
    assert re.search(r"inlineMath\s*:", config)
    assert "['$', '$']" in config
    assert r"['\\(', '\\)']" in config
    assert loader.get("src") == "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"
    assert "async" in loader


def test_assurance_equation_remains_a_display_block() -> None:
    markdown = (DOCS / "qa" / "qa_refactor_plan.md").read_text(encoding="utf-8")
    assert re.search(r"\n\n\$\$\nSpecAssurance[^\n]+\n\$\$\n\n", markdown)


@pytest.fixture(scope="module")
def docs_site(tmp_path_factory: pytest.TempPathFactory) -> Iterator[str]:
    bundle = shutil.which("bundle")
    if bundle is None:
        pytest.fail("Bundler is required on PATH to run DOCS_LIVE_TESTS=1")

    site = tmp_path_factory.mktemp("docs-site")
    result = subprocess.run(
        [bundle, "exec", "jekyll", "build", "--destination", str(site)],
        cwd=DOCS,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
    )
    if result.returncode:
        pytest.fail(f"Jekyll build failed:\n{result.stdout[-5000:]}\n{result.stderr[-5000:]}")
    handler = functools.partial(DocsRequestHandler, directory=str(site))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


@pytest.fixture(scope="module")
def browser() -> Iterator:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        pytest.fail('Install browser test dependencies: python -m pip install -e ".[docs-test]"')

    with sync_playwright() as playwright:
        channel = os.environ.get("DOCS_BROWSER_CHANNEL")
        instance = playwright.chromium.launch(channel=channel)
        try:
            yield instance
        finally:
            instance.close()


def _wait_for_mathjax(page, failures: list[str]) -> float:
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

    try:
        page.wait_for_function("() => !!window.MathJax?.startup?.promise", timeout=20_000)
    except PlaywrightTimeoutError as error:
        raise AssertionError(f"MathJax did not start; CDN failures: {failures}") from error
    return page.evaluate("async () => { await window.MathJax.startup.promise; return performance.now(); }")


def _observe_cdn(context) -> list[str]:
    failures: list[str] = []

    def on_failed(request) -> None:
        if "cdn.jsdelivr.net/npm/mathjax@" in request.url:
            failures.append(f"{request.url}: {request.failure}")

    def on_response(response) -> None:
        if "cdn.jsdelivr.net/npm/mathjax@" in response.url and response.status >= 400:
            failures.append(f"{response.url}: HTTP {response.status}")

    context.on("requestfailed", on_failed)
    context.on("response", on_response)
    return failures


@pytest.mark.docs_live
@pytest.mark.skipif(not LIVE_ENABLED, reason="Set DOCS_LIVE_TESTS=1 to run live documentation checks")
def test_live_cdn_renders_display_and_inline_equations(docs_site: str, browser) -> None:
    context = browser.new_context()
    failures = _observe_cdn(context)
    try:
        page = context.new_page()
        page.goto(f"{docs_site}/qa/qa_refactor_plan.html", wait_until="domcontentloaded")
        _wait_for_mathjax(page, failures)
        assert page.locator("mjx-container[display='true'] mjx-mfrac").count() == 1
        assert page.locator("mjx-merror").count() == 0

        page.goto(f"{docs_site}/qa/score_comparison_1.html", wait_until="domcontentloaded")
        _wait_for_mathjax(page, failures)
        assert page.locator("mjx-container:not([display='true'])").count() == 2
        assert page.locator("mjx-merror").count() == 0

        page.goto(f"{docs_site}/qa/score_comparison_2.html", wait_until="domcontentloaded")
        _wait_for_mathjax(page, failures)
        assert page.locator("mjx-container:not([display='true'])").count() == 1
        assert page.locator("mjx-merror").count() == 0

        page.goto(f"{docs_site}/progress/phase-1b/PHASE_1b_CI_CD_SETUP.html", wait_until="domcontentloaded")
        _wait_for_mathjax(page, failures)
        assert page.locator("pre code").filter(has_text="${{ matrix.python-version }}").count() == 1
        assert page.locator("pre mjx-container").count() == 0
        assert not failures, f"MathJax CDN requests failed: {failures}"
    finally:
        context.close()


@pytest.mark.docs_live
@pytest.mark.skipif(not LIVE_ENABLED, reason="Set DOCS_LIVE_TESTS=1 to run live documentation checks")
def test_page_remains_readable_when_mathjax_is_unavailable(docs_site: str, browser) -> None:
    context = browser.new_context()
    failures = _observe_cdn(context)
    context.route("**/npm/mathjax@3/**", lambda route: route.abort())
    try:
        page = context.new_page()
        page.goto(f"{docs_site}/qa/score_comparison_1.html", wait_until="load")
        assert failures, "The test did not block a MathJax CDN request"
        assert page.locator("main").is_visible()
        assert page.locator("main").inner_text().find(r"\mathbf{45.24\%}") >= 0
        assert page.locator("mjx-container").count() == 0
    finally:
        context.close()


@pytest.mark.docs_live
@pytest.mark.skipif(not LIVE_ENABLED, reason="Set DOCS_LIVE_TESTS=1 to run live documentation checks")
def test_cold_math_page_timing_against_non_math_page(docs_site: str, browser) -> None:
    samples: dict[str, list[float]] = {"non-math": [], "math": []}
    for _ in range(5):
        for label, path in (("non-math", "/"), ("math", "/qa/score_comparison_1.html")):
            context = browser.new_context()
            failures = _observe_cdn(context)
            try:
                page = context.new_page()
                response = page.goto(f"{docs_site}{path}", wait_until="load")
                assert response is not None and response.ok
                elapsed = _wait_for_mathjax(page, failures)
                assert not failures, f"MathJax CDN requests failed: {failures}"
                assert page.locator("mjx-merror").count() == 0
                if label == "math":
                    assert page.locator("mjx-container").count() == 2
                else:
                    assert page.locator("mjx-container").count() == 0
                samples[label].append(elapsed)
            finally:
                context.close()

    non_math_ms = statistics.median(samples["non-math"])
    math_ms = statistics.median(samples["math"])
    limit_ms = 2 * non_math_ms + 1000
    print(
        f"Cold load through MathJax startup: non-math={non_math_ms:.0f} ms, "
        f"math={math_ms:.0f} ms, limit={limit_ms:.0f} ms"
    )
    assert math_ms <= limit_ms
