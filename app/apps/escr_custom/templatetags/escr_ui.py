"""
Small helpers for our Django templates ({% load escr_ui %}):

- {% icon "cpu" %}: a Lucide icon (https://lucide.dev, ISC licence), drawn
  like the Vue UI's. The shapes are copied from the lucide package the front
  end uses; add one here when a template needs it.
- {{ value|minutes }}: CPU/GPU minutes, as precise as their size needs.
"""
from django import template
from django.utils.html import format_html, format_html_join

register = template.Library()

ICONS = {
    'hard-drive': [
        ('path', {'d': 'M10 16h.01'}),
        ('path', {'d': 'M2.212 11.577a2 2 0 0 0-.212.896V18a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-5.527a2 2 0 0 0-.212-.896L18.55 5.11A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z'}),
        ('path', {'d': 'M21.946 12.013H2.054'}),
        ('path', {'d': 'M6 16h.01'}),
    ],
    'cpu': [
        ('path', {'d': 'M12 20v2'}), ('path', {'d': 'M12 2v2'}),
        ('path', {'d': 'M17 20v2'}), ('path', {'d': 'M17 2v2'}),
        ('path', {'d': 'M2 12h2'}), ('path', {'d': 'M2 17h2'}), ('path', {'d': 'M2 7h2'}),
        ('path', {'d': 'M20 12h2'}), ('path', {'d': 'M20 17h2'}), ('path', {'d': 'M20 7h2'}),
        ('path', {'d': 'M7 20v2'}), ('path', {'d': 'M7 2v2'}),
        ('rect', {'x': '4', 'y': '4', 'width': '16', 'height': '16', 'rx': '2'}),
        ('rect', {'x': '8', 'y': '8', 'width': '8', 'height': '8', 'rx': '1'}),
    ],
    'zap': [
        ('path', {'d': 'M15.914 4a1.5 1.5 0 00-2.474-1.561l-9 9A1.5 1.5 0 005.5 14h4.002a.5.5 0 01.471.666L8.086 20a1.5 1.5 0 002.475 1.56l9-9A1.5 1.5 0 0018.5 10h-3.997a.5.5 0 01-.472-.667z'}),
    ],
    'circle-check': [
        ('circle', {'cx': '12', 'cy': '12', 'r': '10'}),
        ('path', {'d': 'm16 9-5.5 5.5L8 12'}),
    ],
    'circle-x': [
        ('circle', {'cx': '12', 'cy': '12', 'r': '10'}),
        ('path', {'d': 'm15 9-6 6'}), ('path', {'d': 'm9 9 6 6'}),
    ],
    'loader-circle': [
        ('path', {'d': 'M21 12a9 9 0 1 1-6.219-8.56'}),
    ],
    'circle-dashed': [
        ('path', {'d': 'M10.1 2.182a10 10 0 0 1 3.8 0'}),
        ('path', {'d': 'M13.9 21.818a10 10 0 0 1-3.8 0'}),
        ('path', {'d': 'M17.609 3.721a10 10 0 0 1 2.69 2.7'}),
        ('path', {'d': 'M2.182 13.9a10 10 0 0 1 0-3.8'}),
        ('path', {'d': 'M20.279 17.609a10 10 0 0 1-2.7 2.69'}),
        ('path', {'d': 'M21.818 10.1a10 10 0 0 1 0 3.8'}),
        ('path', {'d': 'M3.721 6.391a10 10 0 0 1 2.7-2.69'}),
        ('path', {'d': 'M6.391 20.279a10 10 0 0 1-2.69-2.7'}),
    ],
    'ban': [
        ('circle', {'cx': '12', 'cy': '12', 'r': '10'}),
        ('path', {'d': 'M4.929 4.929 19.07 19.071'}),
    ],
    'info': [
        ('circle', {'cx': '12', 'cy': '12', 'r': '10'}),
        ('path', {'d': 'M12 16v-4'}), ('path', {'d': 'M12 8h.01'}),
    ],
    'clock': [
        ('circle', {'cx': '12', 'cy': '12', 'r': '10'}),
        ('path', {'d': 'M12 6v6l4 2'}),
    ],
    'arrow-left': [
        ('path', {'d': 'm12 19-7-7 7-7'}), ('path', {'d': 'M19 12H5'}),
    ],
    'file-text': [
        ('path', {'d': 'M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z'}),
        ('path', {'d': 'M14 2v5a1 1 0 0 0 1 1h5'}),
        ('path', {'d': 'M10 9H8'}), ('path', {'d': 'M16 13H8'}), ('path', {'d': 'M16 17H8'}),
    ],
}


@register.simple_tag
def icon(name, size=16, css_class=''):
    """An inline, decorative (aria-hidden) Lucide icon."""
    nodes = format_html_join(
        '', '<{} {}/>',
        ((tag, format_html_join(' ', '{}="{}"', attrs.items())) for tag, attrs in ICONS[name]),
    )
    return format_html(
        '<svg class="escr-icon {}" xmlns="http://www.w3.org/2000/svg" width="{}" height="{}" '
        'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" '
        'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">{}</svg>',
        css_class, size, size, nodes,
    )


@register.filter
def minutes(value):
    """1234.5 -> "1,235", 12.34 -> "12.3", 0.0123 -> "0.01", tiny -> "<0.01"."""
    value = float(value or 0)
    if value == 0:
        return '0'
    if value < 0.01:
        return '<0.01'
    if value < 10:
        return f'{value:.2f}'
    if value < 100:
        return f'{value:.1f}'
    return f'{value:,.0f}'
