
# RixFlix [![License](https://img.shields.io/badge/license-CC--NC--SA%204.0-green)](http://creativecommons.org/licenses/by-nc-sa/4.0/)

RixFlix is Rick Ryan's performance-focused Kodi skin for the Ugoos AM9. It is a
fork of [Arctic Fuse 3](https://github.com/jurialmunkey/skin.arctic.fuse.3) by
Jurial Munkey and retains that project's full Git history.

The add-on id is `skin.rixflix`, deliberately separate from upstream. Both skins
can remain installed for measured A/B tests and immediate rollback. RixFlix's
AM9 deployment policy, live probes, and recovery tooling live in the
[`Rixflix`](https://github.com/RickRyan26/Rixflix) repository.

Version 1.1 makes the RixFlix wordmark and textures native skin assets, uses the
bounded AM9 Kodi restart controller in the default power menu, and disables the
measured adaptive blur/crop transition cost while retaining TMDb Helper metadata.
Version 1.1.1 makes those case-sensitive Kodi setting resets use their canonical
lowercase ids, verified by a true -> restart -> false test on the AM9.
Version 1.2 gives the real startup overlay a deterministic full-screen RixFlix splash
and native busy badge, while removing the unrelated weather fanart/temperature work.
Profile-login screens retain their lightweight RixFlix wordmark and custom background.

This work is licensed under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 Unported License. To view a copy of this license, visit http://creativecommons.org/licenses/by-nc-sa/4.0/
or send a letter to Creative Commons, 171 Second Street, Suite 300, San Francisco, California, 94105, USA.
