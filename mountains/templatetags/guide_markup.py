from django import template
from django.utils.html import conditional_escape, format_html, mark_safe

register = template.Library()


@register.filter
def guide_markup(value):
    if value is None:
        return ""

    escape = conditional_escape
    blocks = str(value).split("\n\n")
    rendered = []

    for block in blocks:
        text = block.strip()
        if not text:
            continue
        if text.startswith("### "):
            rendered.append(format_html("<h3>{}</h3>", text[4:].strip()))
        elif text.startswith("## "):
            rendered.append(format_html("<h2>{}</h2>", text[3:].strip()))
        else:
            rendered.append(format_html("<p>{}</p>", mark_safe("<br>".join(escape(line) for line in text.splitlines()))))

    return mark_safe("".join(rendered))
