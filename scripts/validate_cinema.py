#!/usr/bin/env python3
"""Source-level cinema checks; live navigation still belongs to the AM9 smoke.

Button/label contracts: https://kodi.wiki/view/Button_control
Grouplist pitch (Size = top + height, focus scroll): xbmc/guilib/GUIControlGroupList.cpp
Contrast: https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html
"""
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
CRIMSON = ('e50914', '8c101b')


def params(node):
    return {p.get('name'): p.text for p in node.findall('param')}


def luminance(argb):
    assert argb[:2] == 'ff', 'Action surfaces must be opaque over arbitrary fanart'
    rgb = [int(argb[n:n+2], 16) / 255 for n in (2, 4, 6)]
    linear = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055)**2.4 for v in rgb]
    return sum(v * w for v, w in zip(linear, (0.2126, 0.7152, 0.0722)))


def check_home_rows(constants):
    def num(value):
        return float(constants.get(value, value))

    lists = ET.parse(ROOT / '1080i/Includes_Lists.xml').getroot()
    layouts = ET.parse(ROOT / '1080i/Includes_Layouts.xml').getroot()
    widgets = ET.parse(ROOT / '1080i/Includes_Widgets.xml').getroot()
    rules = ET.parse(ROOT / 'shortcuts/generator/data/setup/widgets_include_row.xml').getroot()

    def rule(name, style):
        return rules.find(f"rules[@name='{name}']/rule[condition='{{item_widget_style}}=={style}']/value").text

    # Search rows share widget_include; Home has its own mapping.
    assert rule('widget_include', 'Poster') == 'List_Poster_Row'
    sizes = {}
    for style, include in (('Premiere', 'List_Premiere_Row'), ('Poster', 'List_Home_Poster_Row'),
                           ('Category', 'List_Category_Row')):
        assert rule('widget_home_include', style) == include, style
        row = params(lists.find(f"include[@name='{include}']/definition/include"))
        w, h, lw = num(row['item_w']), num(row['item_h']), num(row['itemlayout_w'])
        assert lw - w == num('home_row_gap_w') == 16, (include, 'horizontal gap', lw - w)
        assert row['offset_y'] == 'home_row_offset_y', include
        # A scrolled row's previous card must be clipped by the list, not cover the title margin.
        list_l = lists.find(f"include[@name='{include}']/definition/include").findtext('left')
        assert (list_l, row['offset_x']) == ('home_row_list_l', 'home_row_list_offx'), include
        assert widgets.find(f"include[@name='Widget_Busy_BlankItems__{include}']") is not None, include
        assert widgets.findtext(f"include[@name='Widget_Busy_Spinner_Height__{include}']/height") == row['item_h']
        sizes[style] = (w, h)

    # New Releases: the standard poster layout, larger, with no text or ribbon of its own.
    premiere = layouts.find("include[@name='Layout_Premiere']/definition")
    poster = premiere.find("include[@content='Layout_Poster']")
    assert poster is not None and params(poster)['indicator'] == 'false'
    assert not premiere.findall('.//control'), 'New Releases cards are poster art only'
    (pw, ph), (sw, sh) = sizes['Premiere'], sizes['Poster']
    assert pw > sw and ph > sh and abs(pw / ph - sw / sh) < 0.01, 'larger posters, same aspect'

    category = layouts.find("include[@name='Layout_Category']/definition/control")
    text = ET.tostring(category, encoding='unicode').lower()
    assert not any(c in text for c in CRIMSON), 'Categories carry no red styling'
    assert 'EXPLORE' not in text.upper() and 'ListItem.Icon' not in ET.tostring(category, encoding='unicode')
    for layout in (premiere, category):
        assert not layout.findall('.//animation'), 'Home cards must not add per-item animation'

    # Vertical geometry, per Kodi's grouplist: pitch of a child is its top + height.
    hubs = ET.parse(ROOT / '1080i/Includes_Hubs.xml').getroot()
    grouplist = hubs.find("include[@name='Hub_Widgets_Grouplist']/definition/control")
    viewport = 1080 - num(grouplist.findtext('top')) - num(grouplist.findtext('bottom'))
    row_top = num('widget_items_t_detailed')
    assert num('widget_label_h_detailed') == 0
    assert viewport == row_top + num('home_row_h'), ('focused row must scroll to the top', viewport)
    pitch = viewport + num('home_row_label_t')
    card_top = row_top + num('home_row_offset_y')
    assert 16 <= pitch - sh <= 40, ('row gap', pitch - sh)
    assert num('home_row_bump_h') == -num('home_row_label_t'), 'first row starts at the viewport top'
    assert num('home_row_list_l') + num('home_row_list_offx') == num('view_offx'), 'cards stay at x=80'
    assert num('home_row_list_l') == num('view_offx') - num('home_row_gap_w'), 'previous card ends at the list edge'
    assert num('home_row_list_l') >= num('view_pad') + num('home_title_left') + 40 / 2, 'title margin is clear'
    assert num('home_premiere_row_h') - num('home_row_h') == round(ph - sh), 'New Releases pays its own height'
    # Focused rows start at y500 (940 - 440); one full row and most of the next fit.
    assert 500 + pitch + card_top + sh * 0.4 <= 1080, ('at least 40% of the next row must show', pitch)
    # Kodi clips the label's PRE-rotation rect to the grouplist (x >= 0): the rect must
    # start at its rotation anchor (left-aligned, y-centred) and run right, never centre
    # on the margin (1.12.0 theater capture showed "v Releases").
    assert num('home_title_left') + num('view_pad') == 40, 'title line centred in the left margin'
    assert num('home_title_t') + 20 == card_top, 'title starts at the card top'

    template = (ROOT / 'shortcuts/generator/data/parts/widgets_row.xmltemplate').read_text()
    for marker in ('<param name="widgetheight">{widget_home_height}</param>',
                   '<param name="labeltop">home_row_label_t</param>',
                   '<param name="inline_label">true</param>',
                   '<param name="include">{widget_home_include}</param>'):
        assert marker in template, marker
    base = (ROOT / 'shortcuts/generator/data/base/home_widgets_standard.xml').read_text()
    assert 'widgets_grouplist_home.xmltemplate' in base
    bumper = (ROOT / 'shortcuts/generator/data/parts/widgets_grouplist_home.xmltemplate').read_text()
    assert '<param name="bumper_h">home_row_bump_h</param>' in bumper
    # Rows above the focused one fade, so their badges cannot rim the focused row.
    assert ('condition="ControlGroup({grouplist_id}).HasFocus + '
            'Integer.IsGreater(System.CurrentControlId,{widget_id})"') in template
    assert '<value name="grouplist_id">602</value>' in base
    info = ET.parse(ROOT / '1080i/Includes_Info.xml').getroot()
    pills = info.find("include[@name='Info_Line_VideoQuality_Resolution']/definition")
    assert [params(i)['label'] for i in pills if params(i).get('label') == 'TV'] == ['TV'], 'shows get a TV pill'
    title = widgets.find("include[@name='Widget_Inline_Title']/definition/control")
    assert title.findtext('angle') == '-90' and title.findtext('align') == 'left'
    assert title.findtext('aligny') == 'center' and title.findtext('height') == '40'
    assert '{widget_home_title_top}' not in template

    # The rows slide away from a playing New Releases preview, and only react to it.
    slides = [a for a in grouplist.findall('animation') if 'Exp_RixFlix_HomeTrailerShowing' in (a.get('condition') or '')]
    assert len(slides) == 1 and slides[0].get('effect') == 'slide'
    expressions = ET.parse(ROOT / '1080i/Includes_Expressions.xml').getroot()
    showing = expressions.find("expression[@name='Exp_RixFlix_HomeTrailerShowing']").text
    for part in ('Control.HasFocus(501)', 'Player.HasVideo', 'RixFlix.LocalTrailerActiveID', 'Container(501).ListItem.DBID', 'RixFlix.LocalTrailerActiveType'):
        assert part in showing, part
    # Home previews play inside the wallpaper box, never full-frame under the stretched mask.
    background = ET.parse(ROOT / '1080i/Includes_Background.xml').getroot()
    video = background.find("include[@name='Background_Video']")
    home = [g for g in video.findall('control') if g.findtext('visible') == 'Window.IsVisible(home)']
    assert len(home) == 1 and home[0].findtext('include') == 'Background_Video_FlixArt'
    return pitch, sizes


def check_static_content_targets():
    """A runtime-dynamic <content target> deadlocks Kodi RC1: StartDirectoryJob reads it
    under the provider lock on a JobWorker, and that label read waits for the GUI lock
    the main thread holds while waiting in UpdateURL for the same provider lock. Player
    OnPlay/OnStop refresh every provider, so Home previews hit it (theater 2026-10-18)."""
    dynamic = []
    for path in sorted((ROOT / '1080i').glob('*.xml')):
        if path.name == 'FileManager.xml':  # manual browser; no playback-driven refresh
            continue
        root = ET.parse(path).getroot()
        values = [n.get('target') or '' for n in root.iter('content')]
        values += [n.text or '' for n in root.iter('param') if n.get('name') == 'target']
        dynamic += [(path.name, v) for v in values
                    if any(t in v for t in ('$INFO[', '$VAR[', '$ESCINFO['))]
    assert not dynamic, ('dynamic <content target>', dynamic)


def check():
    check_static_content_targets()
    constants = {c.get('name'): (c.text or '').strip()
                 for c in ET.parse(ROOT / '1080i/Includes_Constants.xml').getroot().findall('constant')}
    pitch, sizes = check_home_rows(constants)

    hubs = ET.parse(ROOT / '1080i/Includes_Hubs.xml').getroot()
    template = hubs.find("include[@name='Hub_Spotlight_Button_Cinema']")
    control = template.find('definition/control')
    assert control.get('type') == 'button' and control.find('nested') is not None
    assert len(template.find('definition')) == 1, 'Decorations must not split the action hit area'
    spotlight = hubs.find("include[@name='Hub_Spotlight']/definition/control")
    row = spotlight.find("control[@id='310']")
    buttons = row.findall("include[@content='Hub_Spotlight_Button_Cinema']")
    assert [params(b)['id'] for b in buttons] == ['311'], 'the spotlight has only Play'
    assert spotlight.find("include[@content='View_Line']") is None, 'no spotlight header'
    assert not row.findall("control[@type='group']"), 'Nested focus groups break Left/Right'
    play = buttons[0]
    assert play.find("include[@content='Hub_Spotlight_Button']") is not None
    assert params(play.find("include[@content='Hub_Spotlight_Button']"))['id'] == '311'
    assert 'Hub_Spotlight_OnLeft' in [i.text for i in play.findall('include')]
    on_left = hubs.find("include[@name='Hub_Spotlight_OnLeft']")
    assert any(o.text == 'Control.Move(301,-1)' for o in on_left.findall('onleft')), 'Left = previous title'
    assert any(o.text == 'Control.Move(301,1)' for o in play.findall('onright')), 'Right = next title'
    assert hubs.find("include[@name='Hub_Spotlight_List']/definition/control").get('type') == 'wraplist'
    window = ET.tostring(hubs.find("include[@name='Hub_Window']"), encoding='unicode')
    assert 'Hub_Spotlight_Info' in window, 'the spotlight shows its logo/title and plot'
    assert 'foreground' not in ET.tostring(spotlight, encoding='unicode'), 'no Play Trailer button'
    info = hubs.find("include[@name='Hub_Combined_Info']/control/control[2]/include[@content='Info_Panel']")
    assert params(info)['visible_plot'] == params(info)['visible_meta'] == '!Window.IsActive(home)', 'Home info is title + one line'

    colors = {c.get('name'): c.text for c in ET.parse(ROOT / 'colors/defaults.xml').getroot()}
    ratios = []
    style = params(template) | params(play)
    for ink, surface in (('ink', 'surface'), ('focus_ink', 'focus_surface')):
        light, dark = sorted((luminance(colors[style[ink]]), luminance(colors[style[surface]])), reverse=True)
        ratio = (light + 0.05) / (dark + 0.05)
        assert ratio >= 4.5, (ink, ratio)
        ratios.append(ratio)
    views = ET.parse(ROOT / '1080i/Includes_Views.xml').getroot()
    for name in ('View_Line_Label', 'View_Line_SubLabel'):
        assert len(views.find(f"include[@name='{name}']/control").findall('textcolor')) == 1
    print(f'PASS: Home rows pitch {pitch:g}px, 16px card gap, New Releases {sizes["Premiere"][0]:g}x'
          f'{sizes["Premiere"][1]:g} posters, inline titles, rows slide for previews; '
          f'spotlight Play-only (Left/Right walk 301), {len(ratios)} contrast states (min {min(ratios):.2f}:1)')


if __name__ == '__main__':
    check()
