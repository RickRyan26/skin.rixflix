#!/usr/bin/env python3
"""Source-level cinema checks; live navigation still belongs to the AM9 smoke.

Button/label contracts: https://kodi.wiki/view/Button_control
Grouplist pitch (Size = top + height, focus scroll): xbmc/guilib/GUIControlGroupList.cpp
Contrast: https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html
"""
from pathlib import Path
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

    # Rick 2026-10-18 16:35: rows never move for a preview; New Releases drops to the bottom
    # edge while focused, and the focused-row info (with plot and ends-at) stays up.
    assert not [a for a in grouplist.iter('animation') if 'Trailer' in (a.get('condition') or '')]
    # 1.12.14: Home rows own one 139px effect, not the sum of independent
    # ancestor440/child301 animation lifecycles. Spotlight visuals move separately.
    assert not grouplist.findall('animation'), 'Home must not inherit the old row compensation'
    motion = hubs.findall("include[@name='Hub_Home_Rows_Motion']/animation")
    assert [a.get('end') for a in motion] == ['0,-139', '0,139', '0,-301']
    assert motion[1].get('condition') == '$EXP[Exp_Hubs_Spotlight_SlideDown]'
    # 1.12.16: spotlight state follows focus first; the queued WidgetContainer only off 310/301/602.
    exprs = ET.parse(ROOT / '1080i/Includes_Expressions.xml').getroot()
    assert exprs.find("expression[@name='Exp_Hubs_Spotlight_SlideDown']").text.startswith(
        '[ControlGroup(310).HasFocus | Control.HasFocus(301) | [!ControlGroup(602).HasFocus + ')
    assert hubs.find("expression[@name='Hub_Spotlight_Visible_Expression']").text.startswith('[$EXP[Exp_Hubs_Spotlight_SlideDown] + ')
    assert '<param name="widgetfade_disable">![$EXP[Exp_Hubs_Spotlight_SlideDown]]</param>' in template
    assert all('WidgetContainer),' + str(i) in motion[2].get('condition') for i in (301, 501, 502))
    # 1.12.15: inside 602 the lift keys on focus (same frame as the scroll), not the queued property.
    assert motion[2].get('condition').startswith(
        '[ControlGroup(602).HasFocus + !Control.HasFocus(501) + !Control.HasFocus(502)] | [!ControlGroup(602).HasFocus + ')
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
    for a in motion[1:2] + spot:
        assert (a.get('start'), a.get('time'), a.get('tween'), a.get('easing'), a.get('reversible')) == \
            ('0', '400', 'quadratic', 'inout', 'true'), a.attrib
    # Recently Added: the same landscape card, the standard row height (only the first row
    # may be short: a short second row lands 128px differently by direction).
    assert rule('widget_home_include', 'PremiereFull') == 'List_Premiere_Row'
    assert rule('widget_include', 'PremiereFull') == 'List_Premiere_Row'
    assert rules.find("rules[@name='widget_home_height']/rule[condition='{item_widget_style}==PremiereFull']") is None
    added_bottom = 940 - 440 + num('home_premiere_drop') + card_top + ph
    assert added_bottom == 1060, ('Recently Added cards share the New Releases bottom edge', added_bottom)
    below_added = 940 - 440 + num('home_premiere_drop') + row_top + num('home_row_h') + num('home_row_label_t') + card_top
    assert below_added >= 1080, ('Continue Movies must stay below the screen edge', below_added)
    poster_bottom = 940 - 440 + num('home_premiere_drop') + card_top + ph
    assert poster_bottom == 1060, ('New Releases cards keep the 1.12.9 bottom edge', poster_bottom)
    # The row below stays off screen while New Releases is focused (the cards' row pays its height).
    next_row = 940 - 440 + num('home_premiere_drop') + num('widget_items_t_detailed') + num('home_premiere_row_h') + num('home_row_label_t') + card_top
    assert next_row >= 1080, ('Recently Added must stay below the screen edge', next_row)
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
        assert len(nodes) == 1 and nodes[0].text == f'Action({action},home)', tag
        assert '$EXP[Exp_RixFlix_PreviewUnderBusy]' in nodes[0].get('condition', ''), tag
    assert '$EXP[Exp_RixFlix_PreviewPlaying]' in forward.find('onclick').get('condition')
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
    assert {n.text for n in edit.findall('ondown')} == {'502', '7900'}
    options = ET.parse(ROOT / '1080i/Custom_1170_Dialog_Options.xml').getroot()
    opt = options.find('.//include[@content="DialogView"]')
    assert params(opt)['onback'] == params(opt)['top_onup'] == '7900'
    timer = ET.parse(ROOT / '1080i/Timers.xml').getroot().find("timer[name='rixflix_home_return']")
    assert timer is not None and timer.findall('onstart')[-1].text == 'ActivateWindow(Home)'
    assert any(n.text == 'Dialog.Close(1170,true)' for n in timer.findall('onstart'))
    search_rows = json.loads((ROOT / 'shortcuts/skinvariables-shortcut-searchwidgets.json').read_text())
    assert len(search_rows) == 1 and search_rows[0]['path'] == 'DefaultSearch-All'
    assert search_rows[0]['widget_limit'] == '20'
    # Rick 2026-10-20: horizontal results, so tall posters stop covering the row beneath.
    assert search_rows[0]['widget_style'] == 'Landscape'
    search_rules = ET.parse(ROOT / 'shortcuts/generator/data/setup/search_path.xml').getroot()
    rule = next(r for r in search_rules.find("rules[@name='widget_path']")
                if r.findtext('condition') == '{item_path}==DefaultSearch-All')
    assert rule.findtext('value') == 'plugin://plugin.video.rixflix.providers/?mode=search&amp;q='
    search_template = (ROOT / 'shortcuts/generator/data/parts/search_row_standard.xmltemplate').read_text()
    assert '<ondown>7900</ondown>' in search_template
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
    # 1.12.27: the probe's A/B switches are inert unless their Home property is set.
    background = (ROOT / '1080i/Includes_Background.xml').read_text()
    assert '<visible>String.IsEmpty(Window(Home).Property(RixFlix.MotionNoArt))</visible>' in background
    assert (ROOT / '1080i/Includes_Hubs.xml').read_text().count(
        '| !String.IsEmpty(Window(Home).Property(RixFlix.MotionSpotlightStatic))</visible>') == 2
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
