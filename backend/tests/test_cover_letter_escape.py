"""Tests for LaTeX escaping in cover letter injection."""

from tailorer.cover_letter import _escape_latex, inject_into_template


class TestEscapeLatex:
    def test_escapes_ampersand(self):
        assert _escape_latex("R&D") == r"R\&D"

    def test_escapes_percent(self):
        assert _escape_latex("100%") == r"100\%"

    def test_escapes_underscore(self):
        assert _escape_latex("my_var") == r"my\_var"

    def test_escapes_dollar(self):
        assert "\\$" in _escape_latex("$100k")

    def test_plain_text_unchanged(self):
        assert _escape_latex("Hello world") == "Hello world"


class TestInjectIntoTemplate:
    def test_replaces_placeholder(self):
        template = r"\begin{document}%%BODY%%\end{document}"
        result = inject_into_template(template, "Hello")
        assert "%%BODY%%" not in result
        assert "Hello" in result

    def test_fallback_appends_before_end(self):
        template = r"\begin{document}\end{document}"
        result = inject_into_template(template, "Body text")
        assert "Body text" in result
        assert result.index("Body text") < result.index(r"\end{document}")

    def test_injected_body_is_escaped(self):
        template = r"\begin{document}%%BODY%%\end{document}"
        result = inject_into_template(template, "Q&A about 50% growth")
        assert r"\&" in result
        assert r"\%" in result
