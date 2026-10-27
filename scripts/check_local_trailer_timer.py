"""Source gates for local New/Fresh row hover; YouTube autoplay stays parked."""
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
root = ET.parse(ROOT / '1080i/Timers.xml').getroot()
local = next(t for t in root.findall('timer') if t.findtext('name') == 'rixflix_local_new_release_trailer')
start, stop = local.findtext('start'), local.findtext('stop')
assert local.find('start').get('reset') == 'false'
assert 'Skin.HasSetting(RixFlix.EnableLocalNewReleaseTrailers)' in start
assert all('Control.HasFocus(%d)' % row in start for row in (501, 502, 503, 504)) and 'Window.IsActive(home)' in start
assert '!Player.HasMedia' in start
ROWS = '[Control.HasFocus(501) | Control.HasFocus(502) | Control.HasFocus(503) | Control.HasFocus(504)]'
assert ROWS in start and '!' + ROWS in stop and '!Window.IsActive(home)' in stop
assert 'LocalTrailerFocusID' in stop and 'LocalTrailerFocusType' in stop
assert 'busydialog' in stop
assert '$EXP[' not in start + stop
assert all('RunScript' not in (a.text or '') and 'PlayerControl' not in (a.text or '')
           for a in list(local))
assert any('LocalTrailerSelection' in (a.text or '') for a in local.findall('onstart'))
assert any('ClearProperty(RixFlix.LocalTrailerSelection' in (a.text or '') for a in local.findall('onstop'))
streamed = next(t for t in root.findall('timer') if t.findtext('name') == 'rixflix_spotlight_trailer')
assert 'Skin.HasSetting(RixFlix.EnableAutoplayTrailers)' in streamed.findtext('start')
assert 'EnableAutoplayTrailers' not in start
hubs = ET.parse(ROOT / '1080i/Includes_Hubs.xml').getroot()
for action in hubs.findall('.//onclick'):
    if action.text == 'PlayerControl(Stop)' and 'AutoplayTrailer' in action.get('condition', ''):
        assert 'Player.Filenameandpath' in action.get('condition'), 'Stop requires exact owned path'
print('PASS local-only New Releases timer; parked YouTube gate; exact owned Stop')
