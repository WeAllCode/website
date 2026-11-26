from django.template import Context
from django.template import Template
from django.template import TemplateSyntaxError
from django.test import SimpleTestCase
from django.test import override_settings

from coderdojochi.templatetags.icons import ICONS


def _render(source):
    return Template("{% load icons %}" + source).render(Context())


class IconTagTest(SimpleTestCase):
    def test_every_icon_renders_svg(self):
        for name in ICONS:
            with self.subTest(name=name):
                out = _render(f'{{% icon "{name}" %}}')
                assert out.startswith("<svg "), out[:80]
                assert out.rstrip().endswith("</svg>"), out[-80:]

    def test_decorative_icon_is_hidden(self):
        out = _render('{% icon "bars" %}')
        assert 'aria-hidden="true"' in out, out
        assert 'class="icon"' in out, out
        assert "role=" not in out, out
        assert "aria-label" not in out, out

    def test_label_gives_named_image(self):
        out = _render('{% icon "bars" label="Menu" %}')
        assert 'role="img" aria-label="Menu"' in out, out
        assert 'class="icon"' in out, out
        assert "aria-hidden" not in out, out

    def test_label_is_escaped(self):
        out = Template('{% load icons %}{% icon "bars" label=lbl %}').render(
            Context({"lbl": '"><script>x</script>'})
        )
        assert "<script>" not in out, out
        assert 'aria-label="&quot;&gt;&lt;script&gt;x&lt;/script&gt;"' in out, out

    def test_licence_comment_stripped(self):
        for name in ICONS:
            with self.subTest(name=name):
                assert "<!--" not in _render(f'{{% icon "{name}" %}}')

    @override_settings(DEBUG=True)
    def test_unknown_name_raises_in_debug(self):
        with self.assertRaises(TemplateSyntaxError):  # noqa: PT027
            _render('{% icon "nope" %}')

    @override_settings(DEBUG=True)
    def test_path_is_not_accepted(self):
        with self.assertRaises(TemplateSyntaxError):  # noqa: PT027
            _render('{% icon "vendor/fa-svgs/solid/bars.svg" %}')

    @override_settings(DEBUG=False)
    def test_unknown_name_renders_nothing_in_prod(self):
        assert _render('{% icon "nope" %}') == ""
