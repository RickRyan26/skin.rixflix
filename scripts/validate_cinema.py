#!/usr/bin/env python3
"""Source-level cinema checks; live navigation still belongs to the AM9 smoke.

Button/label contracts: https://kodi.wiki/view/Button_control
Contrast: https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html
"""
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def params(node):
    return {p.get('name'): p.text for p in node.findall('param')}


def luminance(argb):
    assert argb[:2] == 'ff', 'Action surfaces must be opaque over arbitrary fanart'
    rgb = [int(argb[n:n+2], 16) / 255 for n in (2, 4, 6)]
    linear = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055)**2.4 for v in rgb]
    return sum(v * w for v, w in zip(linear, (0.2126, 0.7152, 0.0722)))


def check():
    hubs = ET.parse(ROOT / '1080i/Includes_Hubs.xml').getroot()
    template = hubs.find("include[@name='Hub_Spotlight_Button_Cinema']")
    control = template.find('definition/control')
    assert control.get('type') == 'button' and control.find('nested') is not None
    assert len(template.find('definition')) == 1, 'Decorations must not split the action hit area'
    row = hubs.find("include[@name='Hub_Spotlight']/definition/control/control[@id='310']")
    buttons = row.findall("include[@content='Hub_Spotlight_Button_Cinema']")
    assert [params(b)['id'] for b in buttons] == ['311', '312', '313']
    assert not row.findall("control[@type='group']"), 'Nested focus groups break Left/Right'
    assert buttons[0].findtext('onright') == '312'
    assert buttons[1].findtext('onleft') == '311'
    assert buttons[2].findtext('onleft[2]') == '312'
    for button in buttons:
        nav = button.find("include[@content='Hub_Spotlight_Button']")
        assert params(nav)['id'] == params(button)['id'], 'Info/Back must restore its own action'
    assert 'RixFlix.UnavailableTrailer' in buttons[2].findtext('visible')
    # All three actions and both carousel arrows fit even the skin's 1440px layout.
    defaults = params(template)
    width = sum(int(params(b).get('width', defaults['width'])) for b in buttons)
    assert width + 2 * 40 + 4 * int(row.findtext('itemgap')) <= 1440 - 2 * 80
    colors = {c.get('name'): c.text for c in ET.parse(ROOT / 'colors/defaults.xml').getroot()}
    ratios = []
    for button in buttons:
        style = defaults | params(button)
        for ink, surface in (('ink', 'surface'), ('focus_ink', 'focus_surface')):
            light, dark = sorted((luminance(colors[style[ink]]), luminance(colors[style[surface]])), reverse=True)
            ratio = (light + 0.05) / (dark + 0.05)
            assert ratio >= 4.5, (params(button)['id'], ink, ratio)
            ratios.append(ratio)
    views = ET.parse(ROOT / '1080i/Includes_Views.xml').getroot()
    for name in ('View_Line_Label', 'View_Line_SubLabel'):
        assert len(views.find(f"include[@name='{name}']/control").findall('textcolor')) == 1
    print(f'PASS: 3 direct actions, focus restoration, compact layout, 6 contrast states (min {min(ratios):.2f}:1)')


if __name__ == '__main__':
    check()
