#!/usr/bin/env python3
"""Source-level cinema checks; live navigation still belongs to the AM9 smoke.

Button/label contracts: https://kodi.wiki/view/Button_control
Grouplist pitch (Size = top + height, focus scroll): xbmc/guilib/GUIControlGroupList.cpp
Contrast: https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html
"""
from pathlib import Path
import re
import json
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

    # New Releases (Rick 2026-10-18 21:29): the stock landscape layout at 16:9, shorter
    # than a poster, filled (detailed) and with no labels, badges or ribbon of its own.
    premiere = layouts.find("include[@name='Layout_Premiere']/definition")
    landscape = premiere.find("include[@content='Layout_Landscape']")
    assert landscape is not None
    assert (params(landscape)['indicator'], params(landscape)['detailed'], params(landscape)['badges']) == ('false', 'true', 'false')
    assert not premiere.findall('.//control'), 'New Releases cards are landscape art only'
    stock = layouts.find("include[@name='Layout_Landscape']")
    assert params(stock)['badges'] == 'true', 'other landscape lists keep their badges'
    (pw, ph), (sw, sh) = sizes['Premiere'], sizes['Poster']
    assert abs(pw / ph - 16 / 9) < 0.01 and ph < sh, 'New Releases: 16:9 landscape, shorter than a poster'

    category = layouts.find("include[@name='Layout_Category']/definition/control")
    assert not category.findall(".//control[@type='textbox']"), 'category art supplies the title'
    assert category.find(".//control[@type='image']/texture").text == '$INFO[ListItem.Art(thumb)]'
    cw, ch = sizes['Category']
    assert (cw, ch) == (560, 315)
    category_list = lists.find("include[@name='List_Category_Row']/definition/include")
    assert category_list.findtext('onclick') == 'ActivateWindow(1138)'
    assert 'coming_soon' in category_list.find('onclick').get('condition', '')
    upcoming = ET.parse(ROOT / '1080i/Custom_1138_ComingSoon.xml').getroot()
    assert upcoming.get('id') == '1138'
    assert layouts.find("include[@name='Layout_ComingSoonPoster']") is None
    chip = upcoming.find(".//include[@content='RixFlix_CategoryTitleChip']")
    assert chip.findtext("param[@name='label']") == 'Coming Soon'
    assert (ROOT / 'extras/categories/coming_soon.jpg').is_file()
    assert category_list.findtext('movement') == '2'
    assert 80 + 2 * num('home_category_itemlayout_w') + cw <= 1920 - 16
    for key in ('past_year', 'movies', 'shows', 'reference', 'netflix', 'disney', 'hulu', 'max', 'paramount', 'prime'):
        assert (ROOT / 'extras/categories' / (key + '.jpg')).is_file(), key
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
    assert num('home_row_bump_h') == -num('home_premiere_label_t'), 'first row starts at the viewport top'
    assert num('home_row_list_l') + num('home_row_list_offx') == num('view_offx'), 'cards stay at x=80'
    assert num('home_row_list_l') == num('view_offx') - num('home_row_gap_w'), 'previous card ends at the list edge'
    assert num('home_row_list_l') >= num('view_pad') + num('home_title_left') + 40 / 2, 'title margin is clear'
    assert num('home_premiere_row_h') == num('home_row_h'), 'every row remains viewport-height'
    landscape_pitch = viewport + num('home_premiere_label_t')
    assert landscape_pitch - ph == 25, 'landscape gutter matches poster gutter'
    premiere_list = lists.find("include[@name='List_Premiere_Row']/definition/include")
    movement = int(premiere_list.findtext('movement'))
    assert num('view_offx') + movement * num('home_premiere_itemlayout_w') + pw <= 1920 - num('home_row_gap_w'), 'last focused card fits'
    # Focused rows start at y500 (940 - 440); one full row and most of the next fit.
    assert 500 + pitch + card_top + sh * 0.4 <= 1080, ('at least 40% of the next row must show', pitch)
    # Kodi clips the label's PRE-rotation rect to the grouplist (x >= 0): the rect must
    # start at its rotation anchor (left-aligned, y-centred) and run right, never centre
    # on the margin (1.12.0 theater capture showed "v Releases").
    assert num('home_title_left') + num('view_pad') == 40, 'title line centred in the left margin'
    assert num('home_title_t') + 20 == card_top, 'title starts at the card top'

    template = (ROOT / 'shortcuts/generator/data/parts/widgets_row.xmltemplate').read_text()
    for marker in ('<param name="widgetheight">{widget_home_height}</param>',
                   '<param name="labeltop">{widget_home_labeltop}</param>',
                   '<param name="inline_label">true</param>',
                   '<param name="include">{widget_home_include}</param>'):
        assert marker in template, marker
    base = (ROOT / 'shortcuts/generator/data/base/home_widgets_standard.xml').read_text()
    assert 'widgets_grouplist_home.xmltemplate' in base
    bumper = (ROOT / 'shortcuts/generator/data/parts/widgets_grouplist_home.xmltemplate').read_text()
    assert '<param name="bumper_h">home_row_bump_h</param>' in bumper
    # Rows above the focused one fade, so their badges cannot rim the focused row.
    # Under a modal (Options) Home's own WidgetContainer decides, or every row fades (1.12.39).
    assert ('condition="ControlGroup({grouplist_id}).HasFocus + '
            '[[!System.HasActiveModalDialog + Integer.IsGreater(System.CurrentControlId,{widget_id})] | '
            '[System.HasActiveModalDialog + Integer.IsGreater(Window.Property(TMDbHelper.WidgetContainer),{widget_id})]]"') in template
    assert '<value name="grouplist_id">602</value>' in base
    info = ET.parse(ROOT / '1080i/Includes_Info.xml').getroot()
    detail = info.find("include[@name='Info_Panel']/definition/control")
    source = next(c for c in detail.findall('control') if c.find("control/label") is not None and 'RixFlix.Quality' in c.findtext('control/label'))
    assert source.findtext('height') == '64'
    assert '$PARAM[include_details]' in source.findtext('visible')
    assert 'RixFlix.Quality' not in source.findtext('visible'), 'late facts must not move the plot'
    # Every Home panel's worst-case content must fit its box: a grouplist silently skips
    # a child that does not fit (1.13.1 spotlight lost "Ends at"). Worst case = spacer 20
    # + title slot + facts line + quality + the larger plot variant + Ends-at row.
    # The first <height> in a group wins, as Kodi applies it.
    meta_h = 60  # Info_Meta's movie/show row group

    def plot_content(max_h, max_h_heading):
        return 20 + num('info_title_h') + 36 + 64 + max(int(max_h), 40 + int(max_h_heading)) + meta_h

    fitted = []
    for owner in hubs.iter('include'):
        name = owner.get('name')
        defaults = params(owner)
        for group in owner.iter('control'):
            panel = next((i for i in group.findall('include') if i.get('content') == 'Info_Panel'), None)
            if panel is None or params(panel).get('home_plot') != 'true':
                continue
            p = {k: re.sub(r'\$PARAM\[(\w+)\]', lambda m: defaults.get(m.group(1), m.group(0)), v or '')
                 for k, v in params(panel).items()}
            content = plot_content(p['home_plot_max_h'], p['home_plot_max_h_heading'])
            box = group.findtext('height')
            assert box is not None and int(box) >= content, (
                'Home panel content overflows its box; "Ends at" would vanish', name, box, content)
            fitted.append(name)
    assert sorted(fitted) == ['Hub_Combined_Info', 'Hub_Spotlight_Info'], fitted

    # Rick 2026-11-11: the row panel's plot ran into the Continue (poster) cards. The row
    # panel's content starts at y60 (view_pad - 20 grouplist top); each style's budget must
    # end above its own first card (cards end at y887: poster top 516, landscape 644).
    rules = ET.parse(ROOT / 'shortcuts/generator/data/setup/widgets_include_row.xml').getroot()
    def rule(name, style):
        for r in rules.find("rules[@name='%s']" % name).findall('rule'):
            cond = r.findtext('condition')
            if cond == 'True' or cond == '{item_widget_style}==' + style:
                return r.findtext('value')
    card_tops = {'Poster': 500 + card_top, 'Premiere': 887 - ph, 'PremiereFull': 887 - ph}
    info_template = (ROOT / 'shortcuts/generator/data/parts/widgets_combined_info_home.xmltemplate').read_text()
    for key in ('variant', 'max_h', 'max_h_heading'):
        assert '{widget_home_plot_%s}' % key in info_template, key
    combined_box = int(hubs.find("include[@name='Hub_Combined_Info']/definition/control/control[2]").findtext('height'))
    for style, top in card_tops.items():
        content = plot_content(rule('widget_home_plot_max_h', style), rule('widget_home_plot_max_h_heading', style))
        assert 60 + content <= top, ('row info runs into the cards', style, 60 + content, top)
        assert content <= combined_box, ('row info exceeds its box', style, content, combined_box)
    assert rule('widget_home_plot_variant', 'Poster') == 'RowPoster' and rule('widget_home_plot_variant', 'Premiere') == 'Row'
    line = detail.find("include[@content='Info_Line']")
    assert params(line)['height'] == '36'
    assert params(detail.find("include[@content='Info_Meta']"))['visible'] == '$PARAM[visible_meta]'
    dialog = ET.parse(ROOT / '1080i/DialogVideoInfo.xml').getroot()
    surface = dialog.find('controls/control')
    assert surface.find('texture').get('colordiffuse') == 'ff080808'
    assert surface.findtext('width') == '1920' and surface.findtext('height') == '1080'
    pills = info.find("include[@name='Info_Line_VideoQuality_Resolution']/definition")
    assert [params(i)['label'] for i in pills if params(i).get('label') == 'TV'] == ['TV'], 'shows get a TV pill'
    title = widgets.find("include[@name='Widget_Inline_Title']/definition/control")
    assert title.findtext('angle') == '-90' and title.findtext('align') == 'left'
    assert title.findtext('aligny') == 'center' and title.findtext('height') == '40'
    assert '{widget_home_title_top}' not in template

    # Rick 2026-10-18 16:35: rows never move for a preview; New Releases drops to the bottom
    # edge while focused, and the focused-row info (with plot and ends-at) stays up.
    assert not [a for a in grouplist.iter('animation') if 'Trailer' in (a.get('condition') or '')]
    # 1.12.14: Home rows own one 139px effect, not the sum of independent
    # ancestor440/child301 animation lifecycles. Spotlight visuals move separately.
    assert not grouplist.findall('animation'), 'Home must not inherit the old row compensation'
    motion = hubs.findall("include[@name='Hub_Home_Rows_Motion']/animation")
    assert [a.get('end') for a in motion] == ['0,-312', '0,312', '0,-128']
    assert motion[1].get('condition') == '$EXP[Exp_Hubs_Spotlight_SlideDown]'
    # 1.12.16: spotlight state follows focus first; the queued WidgetContainer only off 310/301/602.
    exprs = ET.parse(ROOT / '1080i/Includes_Expressions.xml').getroot()
    assert exprs.find("expression[@name='Exp_Hubs_Spotlight_SlideDown']").text.startswith(
        '[ControlGroup(310).HasFocus | Control.HasFocus(301) | [!ControlGroup(602).HasFocus + ')
    assert hubs.find("expression[@name='Hub_Spotlight_Visible_Expression']").text.startswith('[$EXP[Exp_Hubs_Spotlight_SlideDown] + ')
    assert '<param name="widgetfade_disable">![$EXP[Exp_Hubs_Spotlight_SlideDown]]</param>' in template
    assert all('WidgetContainer),' + str(i) in motion[2].get('condition') for i in (301, 501, 502, 503, 504))
    # 1.12.15: inside 602 the lift keys on focus (same frame as the scroll), not the queued property.
    assert motion[2].get('condition').startswith(
        '[ControlGroup(602).HasFocus + !Control.HasFocus(501) + !Control.HasFocus(502) + !Control.HasFocus(503) + !Control.HasFocus(504)] | [!ControlGroup(602).HasFocus + ')
    # 1.12.17: Home 602 scrolls on the grouplist default (400ms quadratic, Kodi's default ease
    # out) and the lift that coincides with it eases out too. An in-out scroll (1.12.15) made
    # every row change a slow start then a rush.
    assert hubs.find("include[@name='Hub_Home_Rows_Scroll']") is None
    assert hubs.find(".//control[@id='602']/scrolltime") is None
    defaults = ET.parse(ROOT / '1080i/Includes_Defaults.xml').getroot()
    scroll = defaults.find("default[@type='grouplist']/scrolltime")
    assert (scroll.text, scroll.get('tween'), scroll.get('easing')) == ('400', 'quadratic', None), scroll.attrib
    assert (motion[2].get('time'), motion[2].get('tween'), motion[2].get('easing')) == ('400', 'quadratic', 'out')
    spot = hubs.findall("include[@name='Hub_Spotlight_Motion']/animation")
    assert len(spot) == 1 and spot[0].get('end') == '0,440', spot
    spotlight = hubs.find("include[@name='Hub_Spotlight']/definition")
    assert not spotlight.findall('animation'), '440px must not be injected into Home group400'
    assert spotlight.find('control/include').get('condition') == '$PARAM[isolated_motion]'
    assert '<param name="home_motion">true</param>' in bumper
    home = ET.parse(ROOT / '1080i/Home.xml').getroot()
    assert home.find('.//param[@name="isolated_spotlight_motion"]').text == 'true'
    ancestor = hubs.find('.//include[.="Hub_Window_Slide_OnSpotlight"]')
    assert '![$PARAM[isolated_spotlight_motion]]' in ancestor.get('condition')
    # 1.12.32: sine, not quadratic. Kodi's QuadTweener EASE_INOUT reaches the end at the
    # midpoint and restarts from the start (Tween.h: no /2, no start offset), which snapped
    # both slides back at 200 ms: the Play <-> New Releases jitter (theater 81146e57081ab571).
    for a in motion[1:2] + spot:
        assert (a.get('start'), a.get('time'), a.get('tween'), a.get('easing'), a.get('reversible')) == \
            ('0', '400', 'sine', 'inout', 'true'), a.attrib
    for xml in sorted((ROOT / '1080i').glob('*.xml')):
        root = ET.parse(xml).getroot()
        for anim in [*root.iter('animation'), *root.iter('effect')]:
            assert not (anim.get('tween') == 'quadratic' and anim.get('easing') == 'inout'), (xml.name, anim.attrib)
    # Recently Added: the same landscape card, the standard row height (only the first row
    # may be short: a short second row lands 128px differently by direction).
    assert rule('widget_home_include', 'PremiereFull') == 'List_Premiere_Row'
    assert rule('widget_include', 'PremiereFull') == 'List_Premiere_Row'
    assert rules.find("rules[@name='widget_home_height']/rule[condition='{item_widget_style}==PremiereFull']") is None
    assert rule('widget_home_labeltop', 'Premiere') == 'home_premiere_label_t'
    assert rule('widget_home_labeltop', 'PremiereFull') == 'home_premiere_label_t'
    landscape_top = 940 - 440 + num('home_premiere_drop') + card_top
    assert landscape_top + ph == round(500 + card_top + sh) == 887, 'same card bottom for every style'
    assert 1080 - (landscape_top + landscape_pitch) >= ph * .5, 'next landscape row peeks into view'
    # 1.12.48: Continue Movies follows Fresh Shows at the landscape gutter, not 128px lower.
    lead = rules.find("rules[@name='widget_home_labeltop']/rule[condition='{item_widget_labeltop}==Premiere']/value")
    assert lead is not None and lead.text == 'home_premiere_label_t', 'Continue Movies keeps the 25px gutter'
    info = hubs.find("include[@name='Hub_Combined_Info']")
    assert 'Trailer' not in ET.tostring(info, encoding='unicode')
    panel = params(info.findall('.//include[@content="Info_Panel"]')[-1])
    assert (panel['visible_plot'], panel['visible_meta']) == ('true', 'true'), 'every row shows the plot'
    furniture = ET.parse(ROOT / '1080i/Includes_Furniture.xml').getroot()
    assert '!$EXP[Exp_RixFlix_PreviewPlaying]' in furniture.find("include[@name='Furniture_Player']/control").findtext('visible')
    # 1.12.18: everything in the bottom-right corner sits on the opaque rounded card: the
    # Now Playing footer, labelled toasts, and a label-less busy spinner (its own small card).
    def cards(node):
        return [i for i in node.iter('control') if i.get('type') == 'image'
                and (i.find('texture') is not None) and i.find('texture').text == 'common/box.png'
                and i.find('texture').get('colordiffuse') == 'rix_cinema_surface']
    player_card = cards(furniture.find("include[@name='Furniture_Player']/control"))
    assert player_card and player_card[0] is furniture.find("include[@name='Furniture_Player']/control/control"), \
        'Now Playing card must sit behind the title and ring'
    # 1.12.21: no Now Playing card while the video plays behind; its text skips the divider.
    player = furniture.find("include[@name='Furniture_Player']/control")
    assert '$EXP[Exp_Video_IsNotPlaying]' in [v.text for v in player.findall('visible')]
    # 1.12.45: nor for any part of an owned hover preview (it opens and closes without HasVideo).
    assert 'String.IsEmpty(Window(Home).Property(RixFlix.LocalTrailerActive))' in \
        [v.text for v in player.findall('visible')], 'empty Now Playing card over a preview open/close'
    floating = [i for i in player.iter('include') if i.get('content') == 'Furniture_Busy_FloatingText']
    assert [i.findtext("param[@name='divider_visible']") for i in floating] == ['false'], floating
    busy = cards(furniture.find("include[@name='Furniture_Busy_Main']"))
    assert sorted(c.findtext('visible') for c in busy) == ['![$PARAM[haslabel]]', '$PARAM[haslabel]'], busy
    # Home previews play in a right-anchored box larger than the fanart, never full-frame.
    background = ET.parse(ROOT / '1080i/Includes_Background.xml').getroot()
    video = background.find("include[@name='Background_Video']")
    home = [g for g in video.findall('control') if g.findtext('visible') == 'Window.IsVisible(home)']
    assert len(home) == 1 and home[0].find('include').get('content') == 'Background_Video_FlixArt'
    box = params(home[0].find('include'))
    assert (num(box['w']), num(box['h'])) == (1600, 900), box
    # The spotlight re-draws on every Home load and never loads the whole library.
    assert 'SetProperty(RixFlix.SpotlightSlot,$VAR[Action_RixFlix_NextSpotlightSlot],Home)' in (ROOT / '1080i/Home.xml').read_text()
    slots = [v.text for v in hubs.findall("variable[@name='Path_RixFlix_HomeSpotlight']/value")][:2]
    assert [Path(t).name for t in slots] == ['RandomSpotlightB.xsp', 'RandomSpotlightA.xsp'], slots
    a, b = ((ROOT / 'extras/playlists' / n).read_text() for n in ('RandomSpotlightA.xsp', 'RandomSpotlightB.xsp'))
    assert a == b and '<limit>30</limit>' in a and '>random</order>' in a
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


def check_hub_conditions():
    """Kodi's InfoExpression treats every `[` as an operator, even inside parentheses, so
    `String.IsEqual(a,$INFO[b])` logs "Misplaced [" and the control stays hidden. The second
    argument takes a bare infolabel. Every category hub row was invisible this way in 1.12.52."""
    hub = (ROOT / '1080i/Includes_CategoryHub.xml').read_text()
    # 1.12.62: a condition per category makes Kodi reload the hub, which alone frees the last page's posters.
    hub_window = (ROOT / '1080i/Custom_1101_Hub.xml').read_text()
    for category in ('past_year', 'movies', 'shows', 'reference', 'netflix', 'disney', 'hulu', 'max', 'paramount', 'prime'):
        assert f'Property(RixFlix.Category),{category})">RixFlix_CategoryHub_Reload<' in hub_window, category
    # 1.12.63: Back reloads the hub with no controls, and only a third window makes that activation real.
    assert 'Property(RixFlix.Category))">RixFlix_CategoryHub<' in hub_window, 'an empty category must load no rows'
    timers = (ROOT / '1080i/Timers.xml').read_text()
    assert ('<onstart>ClearProperty(RixFlix.Category,Home)</onstart>\n'
            '        <onstart>ActivateWindow(1110)</onstart>\n'
            '        <onstart>ActivateWindow(1101)</onstart>\n'
            '        <onstart>ActivateWindow(Home)</onstart>') in timers, 'category Back must free the page before Home'
    assert 'id="1110"' in (ROOT / '1080i/Custom_1110_HubRelease.xml').read_text()
    # 1.14.0: one row definition. The genre row hands it the stale test; the fade itself is shared.
    assert hub.count('<param name="stale">!String.IsEqual(Window(Home).Property(RixFlix.CategoryRow.$PARAM[key]),'
                     'Window(Home).Property(RixFlix.Category))</param>') == 1, (
        'every genre row must stay faded until its own category arrives')
    # CAnimation::Calculate (VisibleEffect.cpp): once its condition clears a fade returns to its
    # START, so start="0" stays black with loaded rows.
    assert hub.count('effect="fade" start="100" end="0" time="200" condition="$PARAM[stale]"') == 1, (
        'a row fade must rest at start="100" or the row never appears')
    assert 'start="0" end="0"' not in hub, 'a conditional start="0" fade never comes back'
    keyboard = (ROOT / '1080i/Dialog_DialogKeyboard.xml').read_text()
    assert 'Control.IsSelected' not in keyboard, 'Kodi has no Control.IsSelected infobool'
    for name in ('Includes_CategoryHub.xml', 'Timers.xml'):
        for node in ET.parse(ROOT / '1080i' / name).getroot().iter():
            boolean = node.tag in ('visible', 'start', 'stop', 'reset') or (
                node.tag == 'param' and node.get('name') in ('visible', 'stale'))
            if boolean:
                assert not re.search(r'\$(INFO|ESCINFO|VAR)\[', node.text or ''), (
                    f'{name}: $INFO inside a boolean expression: {node.text}')


def check_nested_depth():
    """Kodi (CGUIIncludes::InsertNested) fills <nested /> only when it is a definition's top
    node or a direct child of one. Deeper, the caller's children are dropped without any log
    line: 1.14.0's stage rows lost their <content> that way and every list stayed empty."""
    for path in sorted((ROOT / '1080i').glob('*.xml')):
        for include in ET.parse(path).getroot().iter('include'):
            if not include.get('name'):
                continue
            definition = include.find('definition')
            for top in list(definition if definition is not None else include):
                allowed = ([top] if top.tag == 'nested' else []) + top.findall('nested')
                deep = [node for node in top.iter('nested') if node not in allowed]
                assert not deep, f"{path.name}: {include.get('name')} holds a <nested /> Kodi never fills"


def check_end_time_needs_runtime():
    """With no runtime Kodi computes EndTimeResume/FinishTime as the current time, so an
    unreleased Coming Soon title showed "Ends at <now>". Both end-time lines need a runtime."""
    text = (ROOT / '1080i' / 'Includes_Info.xml').read_text()
    lines = [line for line in text.splitlines() if 'name="visible"' in line
             and ('.EndTimeResume)' in line or '.FinishTime)' in line)]
    assert len(lines) == 2, 'expected the two end-time visibility lines'
    for line in lines:
        assert 'Duration(secs),0)' in line, 'an end-time line shows without a runtime'


def check_quality_line_needs_library_item():
    """The quality line is one library file's facts. A Request card has no DBID, so an empty
    QualityDBID matched it and its Information page drew the last library title's quality."""
    text = (ROOT / '1080i' / 'Includes_Info.xml').read_text()
    lines = [line for line in text.splitlines() if '<visible>' in line and 'RixFlix.QualityDBID' in line]
    assert len(lines) == 1, 'expected one quality-line visibility rule'
    assert '!String.IsEmpty($PARAM[container]$PARAM[listitem].DBID)' in lines[0], 'quality line shows without a DBID'
    assert 'Property(RixFlix.RequestKey))' in lines[0], 'quality line shows on a Request title'


def check_request_chip_widths():
    """The Request chip has two pills: 176 for "Requested", 288 for a stage with a date. Exactly
    one may show, so both must test RixFlix.RequestChipWide, in opposite senses."""
    text = (ROOT / '1080i' / 'Includes_Layouts.xml').read_text()
    start = text.index('<include name="Layout_Request">')
    block = text[start:text.index('<include name=', start + 1)] if '<include name=' in text[start + 1:] else text[start:]
    narrow = '!String.IsEmpty(ListItem.Property(RixFlix.RequestChip)) + String.IsEmpty(ListItem.Property(RixFlix.RequestChipWide))'
    wide = '!String.IsEmpty(ListItem.Property(RixFlix.RequestChip)) + !String.IsEmpty(ListItem.Property(RixFlix.RequestChipWide))'
    assert block.count(narrow) == 1 and block.count(wide) == 1, 'Request chip needs one narrow and one wide pill'
    assert block.index(narrow) < block.index('<width>176</width>') < block.index(wide) < block.index('<width>288</width>'), \
        'Request chip pills are not 176 (narrow) then 288 (wide)'


def check_hub_layout(values):
    """1.14.0, the stage: a category page and Coming Soon are Home's row format. One backdrop,
    one Info_Panel above, and two full landscape rows at Home's pitch, from one definition."""
    root = ET.parse(ROOT / '1080i/Includes_CategoryHub.xml').getroot()
    named = lambda name: root.find(f"include[@name='{name}']")
    pitch = int(values['category_row_h'])
    assert pitch == int(values['home_premiere_item_h']) + 25, 'stage pitch must match Home landscape rows'
    # GUIControlGroupList scrolls a focused child to a viewport edge, so only a whole number of
    # pitches keeps every scroll aligned to a row.
    assert int(values['stage_rows_h']) == 2 * pitch, 'the stage viewport must be exactly two rows'
    card_top = int(values['stage_rows_t']) + int(values['category_list_t']) + int(values['home_row_offset_y'])
    assert card_top == 552, 'first card top'
    assert card_top + pitch + int(values['home_premiere_item_h']) <= 1064, 'second row must fit on screen'

    stack = named('RixFlix_Stage_Rows').find('definition/control')
    assert (stack.get('type'), stack.get('id')) == ('grouplist', '$PARAM[id]')
    assert (stack.findtext('top'), stack.findtext('height')) == ('stage_rows_t', 'stage_rows_h')
    assert stack.findtext('itemgap') == '0', 'the row height carries the gutter'
    # The grouplist hands focus back to its last child, so a row aimed at it stays stuck on itself.
    assert (stack.findtext('onup'), stack.findtext('ondown')) == ('noop', 'noop'), 'a sparse page must not wrap'
    assert stack.find('nested') is not None

    row = named('RixFlix_Stage_Row').find('definition/control')
    assert (row.get('type'), row.get('id'), row.findtext('height')) == ('group', '$PARAM[group]', 'category_row_h')
    assert row.find('nested') is not None, 'the row group takes the caller\'s RixFlix_Stage_List'
    # The include is the definition's own top node: only there does Kodi fill its <nested />.
    lists = named('RixFlix_Stage_List').findall("definition/include[@content='List_Premiere_Row']")
    assert len(lists) == 1, 'every stage row is the Home landscape list'
    assert lists[0].findtext('top') == 'category_list_t' and lists[0].find('nested') is not None
    assert (lists[0].findtext('onup'), lists[0].findtext('ondown')) == ('$PARAM[up]', '$PARAM[down]')
    title = row.find("control[@type='label']")
    assert (title.findtext('left'), title.findtext('top'), title.findtext('angle')) == ('40', '0', '-90'), (
        'row titles sit in the left margin as on Home, inside the grouplist clip')

    # Home's own panel for the focused card. Its poster-row budget (tagline + 2 lines, "Ends at"
    # bottom y500, shortcuts/generator widgets_include_row.xml) must clear the first card.
    info = named('RixFlix_Stage_Info').find(".//include[@content='Info_Panel']")
    assert params(info)['container'] == 'Container.', 'one panel follows whichever row has focus'
    assert (params(info)['home_plot'], params(info)['home_plot_variant'], params(info)['home_plot_max_h'],
            params(info)['home_plot_max_h_heading']) == ('true', 'RowPoster', '120', '80')
    assert 500 <= int(values['stage_rows_t']), 'the info panel must end above the row stack'

    # The backdrop: the focused card's fanart, with Home's preview window under it.
    backdrop = named('RixFlix_Stage_Backdrop')
    video = backdrop.find("include[@content='Background_Video_FlixArt']")
    assert (params(video)['w'], params(video)['h']) == ('home_preview_w', 'home_preview_h')
    art = backdrop.find("include[@content='Background_FlixArt']")
    assert params(art)['texture'] == '$VAR[Image_RixFlix_StageArt]'
    assert list(backdrop).index(video) < list(backdrop).index(art), 'the fanart fades out over the preview'
    flixart = ET.parse(ROOT / '1080i/Includes_Background.xml').getroot().find("include[@name='Background_FlixArt']")
    assert params(flixart)['texture'] == '$VAR[Image_Foreground]', 'every other window keeps its own art'
    assert flixart.find('definition/control/include').text == 'Background_NotVideo'
    loading = named('RixFlix_PageLoading').find('definition/control')
    assert loading.findtext('texture') == 'special://skin/media/rixflix/rixflix-wordmark.png'
    assert loading.find('animation').get('pulse') == 'true', 'page loading is the pulsing wordmark'

    def page(children, rows_id, count):
        tags = [(c.text if c.text and c.text.strip() else c.get('content')) for c in children if c.tag == 'include']
        # Both pages hold the one hidden Back button, right after the backdrop.
        order = ['RixFlix_Stage_Backdrop', 'RixFlix_Stage_Return', 'RixFlix_PageLoading', 'RixFlix_Stage_Empty', 'RixFlix_Stage_Info',
                 'RixFlix_Stage_Rows', 'RixFlix_CategoryTitleChip']
        assert tags == order, tags  # drawn in this order: the title card over the rows
        rows = next(c for c in children if c.get('content') == 'RixFlix_Stage_Rows')
        assert params(rows)['id'] == rows_id
        calls = rows.findall('include')
        assert len(calls) == count
        return rows, calls

    hub = named('RixFlix_CategoryHub')
    rows, calls = page(list(hub), '8100', 14)
    assert params(rows)['onback'] == '8900'
    assert all(call.get('content') == 'RixFlix_Category_Row' for call in calls)
    for number, call in enumerate(calls, 1):
        given = params(call)
        assert given['n'] == f'{number:02d}'
        assert given['up'] == (str(8200 + number - 1) if number > 1 else 'noop'), f'row {number} Up'
        assert given['down'] == (str(8200 + number + 1) if number < 14 else 'noop'), f'row {number} Down'
        assert given['key'] == given['label'].replace(' ', '') and given['query'] == given['label'].replace(' ', '%20')
    genre = named('RixFlix_Category_Row').find("definition/include[@content='RixFlix_Stage_Row']")
    assert (params(genre)['id'], params(genre)['group']) == ('81$PARAM[n]', '82$PARAM[n]')
    genre = genre.find("include[@content='RixFlix_Stage_List']")
    assert (params(genre)['id'], params(genre)['up'], params(genre)['down'], params(genre)['onback']) == (
        '81$PARAM[n]', '$PARAM[up]', '$PARAM[down]', '8900')
    content = genre.find('content')
    assert content.get('limit') == '5000' and 'limit=' not in content.text, 'category rows hold the whole genre'
    assert content.text.endswith('&genre=$PARAM[query]')

    upcoming = ET.parse(ROOT / '1080i/Custom_1138_ComingSoon.xml').getroot()
    rows, calls = page(list(upcoming.find('controls')), '8810', 4)
    assert upcoming.findtext('defaultcontrol') == '8820'
    for n, call in enumerate(calls):
        given = params(call)
        assert call.get('content') == 'RixFlix_Stage_Row'
        assert (given['id'], given['group']) == (str(8820 + n), str(8830 + n))
        call = call.find("include[@content='RixFlix_Stage_List']")
        given = params(call)
        assert given['id'] == str(8820 + n)
        assert given['onback'] == '8900', 'Coming Soon Back only focuses the shared return button'
        assert given['up'] == (str(8830 + n - 1) if n else 'noop') and given['down'] == (str(8830 + n + 1) if n < 3 else 'noop')
        assert call.find('content').get('limit') == '5'
        assert f'mode=coming_soon&offset={n*5}&limit=5' in call.findtext('content')
        assert call.findtext('onclick') == (
            f'RunScript(special://skin/scripts/rixflix_trailer.py,$ESCINFO[Container({8820+n}).ListItem.Trailer],foreground)')
    soon_text = (ROOT / '1080i' / 'Custom_1138_ComingSoon.xml').read_text()
    assert not any('ActivateWindow(' in (node.text or '') or 'PreviousMenu' in (node.text or '')
                   for node in ET.fromstring(soon_text).iter()), (
        'a window switch inside onback lets Kodi apply a second Back to the next window')
    assert '<include>RixFlix_Stage_Return</include>' in soon_text
    assert '<onunload>ClearProperty(RixFlix.CategoryReturn.Go,Home)</onunload>' in soon_text
    assert ('        <start reset="true">Window.IsActive(11138) + !String.IsEmpty(Window(Home).Property(RixFlix.CategoryReturn.Go))</start>\n'
            '        <stop>String.IsEmpty(Window(Home).Property(RixFlix.CategoryReturn.Go))</stop>\n'
            '        <onstart>ClearProperty(RixFlix.CategoryReturn.Go,Home)</onstart>\n') in (ROOT / '1080i' / 'Timers.xml').read_text()
    soon_timer = next(t for t in ET.parse(ROOT / '1080i' / 'Timers.xml').getroot().findall('timer')
                      if t.findtext('name') == 'rixflix_coming_soon_return')
    assert [n.text for n in soon_timer.findall('onstart')][1:] == ['SetFocus(8810)', 'ActivateWindow(Home)'], (
        'the page must not keep its focus on the return button: the next visit would bounce Home')
    busy = next(c for c in upcoming.find('controls') if c.get('content') == 'RixFlix_PageLoading')
    assert params(busy)['visible'] == 'Container(8820).IsUpdating + Integer.IsEqual(Container(8820).NumItems,0)'
    assert not upcoming.findall(".//control[@type='label']"), 'no loading sentence: the wordmark is the signal'

    chip = ET.parse(ROOT / '1080i/Includes_CategoryHub.xml').getroot().find(
        "include[@name='RixFlix_CategoryTitleChip']")
    assert 'RixFlix.CategoryLabel' in chip.findtext("param[@name='label']")
    card = chip.find('definition')[-1]
    assert card.get('type') == 'grouplist' and card.findtext('align') == 'right'
    button = card.find("control[@type='button']")
    assert button.findtext('width') == 'auto' and button.findtext('enable') == 'false', 'the title card takes no focus'
    assert button.findtext('label') == '$PARAM[label]'


def check():
    check_hub_conditions()
    check_static_content_targets()
    check_nested_depth()
    check_end_time_needs_runtime()
    check_quality_line_needs_library_item()
    check_request_chip_widths()
    constants = {c.get('name'): (c.text or '').strip()
                 for c in ET.parse(ROOT / '1080i/Includes_Constants.xml').getroot().findall('constant')}
    pitch, sizes = check_home_rows(constants)
    check_hub_layout(constants)

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
    # GUIControlGroupList::AddControl wraps the arrow image's Left back to Play unless the
    # grouplist's own onleft has an action met at load (301 is still empty then).
    for direction in ('onleft', 'onright'):
        assert any(o.text == 'noop' and not o.get('condition') for o in row.findall(direction)), direction
    # Player OnPlay/OnStop re-queries "none"-sorted providers: the spotlight and the RixFlix
    # rows use playlist order, so a preview neither redraws the spotlight nor flashes the rows.
    assert '<param name="spotlight_sortby">$VAR[Sort_RixFlix_HomeSpotlight]</param>' in (ROOT / '1080i/Home.xml').read_text()
    assert [v.text for v in hubs.findall("variable[@name='Sort_RixFlix_HomeSpotlight']/value")][-1] == 'playlist'
    sort_rules = ET.parse(ROOT / 'shortcuts/generator/data/setup/widgets_row.xml').getroot().find("rules[@name='widget_sortby']")
    provider = [r for r in sort_rules.findall('rule') if 'plugin.video.rixflix.providers' in r.findtext('condition')]
    assert len(provider) == 1 and provider[0].findtext('value') == 'playlist'
    spotlight_list = hubs.find("include[@name='Hub_Spotlight_List']/definition/control")
    assert spotlight_list.get('type') == 'wraplist'
    # A modal/player restore may leave focus on offscreen 301 without its onfocus
    # redirect. Vertical/Back keys must recover; horizontal wraplists consume Left/Right.
    assert spotlight_list.findtext('onup') == 'SetFocus(311)'
    assert spotlight_list.findtext('ondown') == '$VAR[Hub_Action_Widgets]'
    assert spotlight_list.findtext('onback') == 'SetFocus(311)'
    assert spotlight_list.find('onclick') is None, 'Play dispatches native Select through 301'
    window = ET.tostring(hubs.find("include[@name='Hub_Window']"), encoding='unicode')
    assert 'Hub_Spotlight_Info' in window, 'the spotlight shows its logo/title and plot'
    assert 'foreground' not in ET.tostring(spotlight, encoding='unicode'), 'no Play Trailer button'

    # Rick 2026-10-18 23:43: no nav bar on Home. Up from the spotlight = search with its
    # keyboard; Back stays on the spotlight (the 300 -> 303 -> Options chain opened 1170
    # over a closing resume menu and blacked out the TV); Down off the last row = Options.
    search = 'RunScript(context.rixflix.gotoshow,opensearch)'
    for node in (row, play):
        ups = [o for o in node.findall('onup') if o.get('condition') == '!Skin.HasSetting(HomeSwitcher.Vertical)']
        assert [o.text for o in ups] == [search], (node.get('id'), [o.text for o in ups])
    button = hubs.find("include[@name='Hub_Spotlight_Button']")
    backs = [o.text for o in button.findall('onback') if o.get('condition') == '$EXP[Exp_RixFlix_NoForegroundMedia]']
    assert backs == ['$PARAM[id]'], backs
    assert '<param name="ondown">ActivateWindow(1170)</param>' in (ROOT / 'shortcuts/generator/data/parts/widgets_grouplist_home.xmltemplate').read_text()
    home_x = ET.parse(ROOT / '1080i/Includes_Home.xml').getroot()
    header = home_x.find("include[@name='Home_Switcher_Horz']").findall('control')[1]
    assert 'Integer.IsEqual(Window(Home).Property(TMDbHelper.WidgetContainer),301)' in header.findtext('visible')
    nav = [g for g in header.findall('control') if g.findtext('visible') == '!Window.IsVisible(Home)']
    assert len(nav) == 1, 'the Search / Home / Settings bar hides on Home'
    assert any(i.text == 'Home_Switcher_Right_Buttons' for i in nav[0].iter('include')), 'gear hides with the bar'
    # 1.12.19: a press during a preview's start-wait busy dialog reaches Home (Rick
    # 2026-10-20 16:15). The focused button forwards it; it must never catch Back.
    busy_dialog = ET.parse(ROOT / '1080i/DialogBusy.xml').getroot()
    forward = busy_dialog.find("controls/control[@id='9100']")
    assert busy_dialog.findtext('defaultcontrol') == '9100' and forward.get('type') == 'button'
    for tag, action in (('onup', 'Up'), ('ondown', 'Down'), ('onleft', 'Left'),
                        ('onright', 'Right'), ('onclick', 'Select')):
        nodes = forward.findall(tag)
        # 1.14.0: one forward per preview surface. A builtin's window argument is the skin's
        # own id (1101); a condition's is Kodi's (11101).
        assert [(n.text, n.get('condition', '').rsplit(' + ', 1)[-1]) for n in nodes] == [
            (f'Action({action},home)', 'Window.IsActive(home)'),
            (f'Action({action},1101)', 'Window.IsActive(11101)'),
            (f'Action({action},1138)', 'Window.IsActive(11138)')], tag
        assert all('$EXP[Exp_RixFlix_PreviewUnderBusy]' in n.get('condition', '') for n in nodes), tag
    assert all('$EXP[Exp_RixFlix_PreviewPlaying]' in n.get('condition') for n in forward.findall('onclick'))
    expressions = (ROOT / '1080i/Includes_Expressions.xml').read_text()
    assert ('<expression name="Exp_RixFlix_PreviewSurface">[Window.IsActive(home) | Window.IsActive(11101) | '
            'Window.IsActive(11138)]</expression>') in expressions
    assert forward.find('onback') is None, 'Back must reach CGUIDialogBusy::OnBack'
    # 1.12.20: caching never opens the timeline (Die My Love, theater 2026-10-20 16:14:
    # each caching flap popped DialogSeekBar in and out). A delayed badge stands in.
    seekbar = ET.parse(ROOT / '1080i/DialogSeekBar.xml').getroot()
    assert not any('Player.Caching' in v.text for v in seekbar.findall('visible')), 'seekbar on caching'
    fullscreen = ET.parse(ROOT / '1080i/VideoFullScreen.xml').getroot()
    badge = [g for g in fullscreen.findall('controls/control') if 'Player.Caching' in (g.findtext('visible') or '')]
    assert len(badge) == 1 and int(badge[0].find("animation[.='Visible']").get('delay')) >= 1000, 'caching badge delay'
    # The bottom-right toast is readable over posters: an opaque card under its text.
    busy = ET.parse(ROOT / '1080i/Includes_Furniture.xml').getroot().find("include[@name='Furniture_Busy_Main']/definition")
    card = busy.find("control[@type='image']")
    colors = {c.get('name'): c.text for c in ET.parse(ROOT / 'colors/defaults.xml').getroot()}
    assert card is not None and colors[card.find('texture').get('colordiffuse')][:2] == 'ff', 'opaque toast card'
    # Rick 2026-10-19: the progress ring sits inside the card's bottom-right corner.
    ring = ET.parse(ROOT / '1080i/Includes_Objects.xml').getroot().find("include[@name='Object_Indicator']/definition/control")
    assert ring.find('centerbottom') is None and int(ring.findtext('bottom')) >= 8 and int(ring.findtext('right')) >= 8
    # Page edges return Home after consuming the movement key. Numeric focus
    # proxies avoid tearing down a window while its OnMove handler still runs.
    search_root = ET.parse(ROOT / '1080i/Includes_Search.xml').getroot()
    edit = search_root.find("include[@name='Search_Bar_Edit']/control[@id='3000']")
    assert edit.findtext('onback') == '7900'
    # 1.12.50: a Down while results load is held for 502, never sent Home.
    downs = {n.text: n.get('condition', '') for n in edit.findall('ondown')}
    assert set(downs) == {'502', '7900', 'SetProperty(RixFlix.SearchDown,1,Home)', 'SetFocus(540)'}, downs
    assert '!$EXP[Exp_RixFlix_Search_Loading]' in downs['7900'], 'empty-results Down must not fire while loading'
    # 1.13.0 Request row (540): Seerr-side titles under Results. Home is only the Down target
    # when neither row has anything; the Request row is reached, never skipped.
    assert '!$EXP[Exp_RixFlix_Request_Ready]' in downs['7900'], 'Down must not go Home past a ready Request row'
    assert '!$EXP[Exp_RixFlix_Search_Loading]' in downs['SetFocus(540)'] and '!$EXP[Exp_RixFlix_Results_Ready]' in downs['SetFocus(540)']
    request = search_root.find("include[@name='Search_Request_Row']/control")
    row = request.find("include[@content='List_Request_Row']")
    assert row.findtext("param[@name='id']") == '540'
    content = row.find('content')
    # Static target and playlist order, as every RixFlix provider row (see deploy.sh's
    # dynamic-target and sortby checks); only the path follows the typed text.
    assert (content.text, content.get('target'), content.get('sortby'), content.get('limit')) == (
        '$VAR[Path_RequestSearch]', 'videos', 'playlist', '20'), content.attrib
    # A click asks Seerr through the provider. Nothing here may play or browse the item.
    assert [n.text for n in row.findall('onclick')] == ['RunPlugin($INFO[Container(540).ListItem.FileNameAndPath])']
    assert [n.text for n in row.findall('ondown')] == ['SetFocus(540)'] and row.findtext('onback') == '7900'
    assert {n.text for n in row.findall('onup')} == {'SetFocus(502)', 'SetFocus(3000)'}
    # 1.13.3: no <visible> on the row or its group. Kodi never loads a hidden container, so a
    # visibility keyed on the row's own items left it empty on the theater box.
    assert row.find('visible') is None and request.find('visible') is None, 'Request row must stay loadable'
    assert any(n.get('condition') == '!$EXP[Exp_RixFlix_Request_Ready]' and n.get('effect') == 'fade'
               for n in request.findall('animation')), 'an unready Request row must be faded out'
    paths = ET.parse(ROOT / '1080i/Includes_Paths.xml').getroot()
    request_path = paths.findtext("variable[@name='Path_RequestSearch']/value")
    # The provider reads the text before "&q=" as its query string; q is a refresh token.
    assert request_path.startswith('plugin://plugin.video.rixflix.providers/?mode=request_search&rev=')
    assert request_path.split('&q=')[0].endswith('&live=1') and request_path.endswith('q=$INFO[Window(Home).Property(RixFlix.SearchCompleted)]'), 'Request must load after Results, not beside it'
    combined = ET.parse(ROOT / '1080i/Includes_Hubs.xml').getroot().find("include[@name='Hub_Combined_Widget']/definition/include")
    hops = [(n.get('condition'), n.text) for n in combined.findall('ondown') if n.get('condition', '').startswith('Window.IsActive(11105)')]
    # Order matters: the row keeps itself first, then hands on when a Request row is ready.
    assert hops == [('Window.IsActive(11105)', 'SetFocus($PARAM[id])'),
                    ('Window.IsActive(11105) + $EXP[Exp_RixFlix_Request_Ready]', 'SetFocus(540)')], hops
    layouts_root = ET.parse(ROOT / '1080i/Includes_Layouts.xml').getroot()
    card = layouts_root.find("include[@name='Layout_Request']/definition/control")
    assert card.find("include[@content='Layout_Landscape']") is not None
    chip = [g for g in card.findall("control[@type='group']") if 'RixFlix.RequestChip' in (g.findtext('visible') or '')]
    # 1.14.10: a narrow pill and a wide one (check_request_chip_widths), same label and colour.
    assert len(chip) == 2, len(chip)
    for pill in chip:
        assert pill.find("control[@type='label']").findtext('label') == '$INFO[ListItem.Property(RixFlix.RequestChip)]'
        assert pill.find("control[@type='image']/texture").get('colordiffuse')[2:] in CRIMSON
    actions = ET.parse(ROOT / '1080i/Includes_Actions.xml').getroot().find("variable[@name='Action_DialogInfo_PlayMedia']")
    first = actions.find('value')
    assert 'RixFlix.RequestKey' in first.get('condition') and first.text == 'RunPlugin($INFO[ListItem.FileNameAndPath])', \
        'Info on a Request title must request, not play'
    window = ET.parse(ROOT / '1080i/Custom_1105_Search.xml').getroot()
    assert 'RunPlugin(plugin://plugin.video.rixflix.providers/?mode=request_open)' in [n.text for n in window.findall('onload')]
    held = ET.parse(ROOT / '1080i/Timers.xml').getroot().find("timer[name='rixflix_search_down']")
    assert held is not None and any(n.text == 'SetFocus(502,0,absolute)' for n in held.findall('onstop'))
    assert '!Window.IsVisible(DialogKeyboard.xml)' in held.findtext('start'), 'focus cannot move under the keyboard'
    assert held.findall('onstop')[-1].text == 'ClearProperty(RixFlix.SearchDown,Home)'
    # 1.12.61: Down off the compact keyboard lands on the first result, not back on the field.
    compact = ET.parse(ROOT / '1080i/Dialog_DialogKeyboard.xml').getroot().find("include[@name='RixFlix_SearchKeyboard']")
    for key_id in ('32', '8', '304'):
        routes = [n.text for n in compact.find(f".//control[@id='{key_id}']").findall('ondown')]
        assert routes == ['SetProperty(RixFlix.SearchDown,1,Home)', 'SendClick(300)'], (key_id, routes)
    # 1.12.49: Down off the keyboard's bottom row is a Done press while search is underneath.
    keys = ET.parse(ROOT / '1080i/Dialog_DialogKeyboard.xml').getroot().find(
        "include[@name='DialogKeyboard_Row_Buttons_SYMBOL']")
    bottom = keys.findall('include')
    assert len(bottom) == 10 and all(
        [(n.text, n.get('condition')) for n in key.findall('ondown')] == [('SendClick(300)', 'Window.IsVisible(11105)')]
        for key in bottom), 'every bottom-row key commits on Down'
    keyboard = ET.parse(ROOT / '1080i/Dialog_DialogKeyboard.xml').getroot()
    compact = keyboard.find("include[@name='RixFlix_SearchKeyboard']/control")
    buttons = [c for c in compact.findall('control') if c.get('type') in ('button', 'radiobutton')]
    assert len(buttons) == 32 and {int(c.get('id')) for c in buttons} == set(range(400, 428)) | {8, 32, 300, 304}
    assert compact.findtext('width') == '628' and compact.findtext('height') == '440'
    assert compact.find("control[@id='300']").findtext('visible') == 'false', 'search is automatic: no visible Done'
    assert not [c for c in compact.findall("control[@type='label']") if c.findtext('label')], 'no hint text row'
    search = ET.parse(ROOT / '1080i/Includes_Search.xml').getroot()
    assert search.find("include[@name='Search_Info_Panel']/control").findtext('visible') == '!Window.IsActive(DialogKeyboard.xml)', 'no hero text beside the keyboard'
    letter_row = [keyboard.find("variable[@name='RixFlix_SearchKey%d']" % i).findall('value')[-1].text for i in range(28)]
    assert ''.join(letter_row) == "ABCDEFGHIJKLMNOPQRSTUVWXYZ-'", 'alphabetical 7 x 4 grid: %r' % letter_row
    assert [compact.find("control[@id='%d']" % i).findtext('label') for i in (32, 8)] == ['SPACE', 'DELETE']
    assert not compact.findall(".//control[@type='list']"), 'Search has no suggestion list'
    assert not [c for c in buttons if c.get('type') == 'radiobutton'], 'a textureless radiobutton draws On/Off over its label'
    assert all(compact.find("control[@id='%d']" % i) is not None for i in (312, 313, 314)), 'native edit/IME controls'
    assert '$ESCINFO' in compact.find("control[@id='312']").findtext('ontextchange')
    assert keyboard.find("include[@name='DialogKeyboard_Full']") is not None
    options = ET.parse(ROOT / '1080i/Custom_1170_Dialog_Options.xml').getroot()
    opt = options.find('.//include[@content="DialogView"]')
    assert params(opt)['onback'] == params(opt)['top_onup'] == '7900'
    timer = ET.parse(ROOT / '1080i/Timers.xml').getroot().find("timer[name='rixflix_home_return']")
    assert timer is not None and timer.findall('onstart')[-1].text == 'ActivateWindow(Home)'
    assert any(n.text == 'Dialog.Close(1170,true)' for n in timer.findall('onstart'))
    search_rows = json.loads((ROOT / 'shortcuts/skinvariables-shortcut-searchwidgets.json').read_text())
    # 1.14.3: the Results heading must follow the LIVE text. Edit 3000 stays empty while the
    # keyboard is open, so a first search (empty field) drew no poster until it closed.
    search_item = (ROOT / 'shortcuts/generator/data/parts/search_item.xmltemplate').read_text()
    assert ('!String.IsEmpty(Control.GetLabel(3000).index(1)) | '
            '!String.IsEmpty(Window(Home).Property(RixFlix.SearchText))') in search_item, \
        'Results heading must show for text typed in the keyboard'
    assert len(search_rows) == 1 and search_rows[0]['path'] == 'DefaultSearch-All'
    assert search_rows[0]['widget_limit'] == '20'
    # Rick 2026-10-20: horizontal results, so tall posters stop covering the row beneath.
    assert search_rows[0]['widget_style'] == 'Landscape'
    search_rules = ET.parse(ROOT / 'shortcuts/generator/data/setup/search_path.xml').getroot()
    rule = next(r for r in search_rules.find("rules[@name='widget_path']")
                if r.findtext('condition') == '{item_path}==DefaultSearch-All')
    assert rule.findtext('value') == 'plugin://plugin.video.rixflix.providers/?mode=search&amp;live='
    search_template = (ROOT / 'shortcuts/generator/data/parts/search_row_standard.xmltemplate').read_text()
    assert '<ondown>SetFocus({widget_id})</ondown>' in search_template
    assert '<onup>SetFocus(3000)</onup>' in search_template
    combined = ET.parse(ROOT / '1080i/Includes_Hubs.xml').getroot().find("include[@name='Hub_Combined_Widget']/definition/include")
    assert next(n.text for n in combined.findall('ondown') if n.get('condition') == 'Window.IsActive(11105)') == 'SetFocus($PARAM[id])'
    assert next(n.text for n in combined.findall('onup') if n.get('condition') == 'Window.IsActive(11105)') == 'SetFocus(3000)'
    # 1.12.25: the seek bar outlives a network seek's 2.0-2.8 s refill (no hide/re-show).
    seekbar = (ROOT / '1080i/DialogSeekBar.xml').read_text()
    assert 'Player.HasPerformedSeek(3)' in seekbar and 'HasPerformedSeek(2)' not in seekbar
    # 1.12.23: the VideoOSD timeline is a button - Up closes the OSD, Select toggles pause.
    timeline = ET.parse(ROOT / '1080i/VideoOSD.xml').getroot().find(".//control[@id='8200']")
    assert timeline.get('type') == 'button', timeline.get('type')
    assert (timeline.findtext('onup'), timeline.findtext('onclick')) == (
        'Dialog.Close(videoosd)', 'PlayerControl(Play)')
    assert (timeline.findtext('onleft'), timeline.findtext('onright')) == (
        'Action(StepBack)', 'Action(StepForward)')
    # 1.12.24: Home carries the probe-gated motion debug strip, hidden unless the probe sets its property.
    home = ET.parse(ROOT / '1080i/Home.xml').getroot()
    assert any(i.text == 'Home_Motion_Debug' for i in home.iter('include'))
    debug = hubs.find("include[@name='Home_Motion_Debug']/control")
    assert debug.findtext('visible') == '!String.IsEmpty(Window(Home).Property(RixFlix.MotionDebug))'
    # 1.12.28: twelve latch bars inside the gated strip, each a non-reversible slide on its condition.
    latch = hubs.find("include[@name='Home_Motion_Debug_Latch']/control/animation")
    assert (latch.get('reversible'), latch.get('condition')) == ('false', '$PARAM[condition]')
    assert sum(i.text == 'Home_Motion_Debug_Latch' or i.get('content') == 'Home_Motion_Debug_Latch'
               for i in debug.iter('include')) == 12
    ratios = []
    style = params(template) | params(play)
    # Rick 2026-10-20 21:13: the spotlight Play is white with black text when focused.
    assert (style['focus_surface'], style['focus_ink']) == ('rix_cinema_paper', 'rix_cinema_ink'), style
    for ink, surface in (('ink', 'surface'), ('focus_ink', 'focus_surface')):
        light, dark = sorted((luminance(colors[style[ink]]), luminance(colors[style[surface]])), reverse=True)
        ratio = (light + 0.05) / (dark + 0.05)
        assert ratio >= 4.5, (ink, ratio)
        ratios.append(ratio)
    views = ET.parse(ROOT / '1080i/Includes_Views.xml').getroot()
    for name in ('View_Line_Label', 'View_Line_SubLabel'):
        assert len(views.find(f"include[@name='{name}']/control").findall('textcolor')) == 1
    print(f'PASS: Home rows pitch {pitch:g}px, 16px card gap, New Releases {sizes["Premiere"][0]:g}x'
          f'{sizes["Premiere"][1]:g} landscape cards, inline titles, previews leave rows in place; '
          f'spotlight Play-only (Left/Right walk 301), {len(ratios)} contrast states (min {min(ratios):.2f}:1)')


if __name__ == '__main__':
    check()
