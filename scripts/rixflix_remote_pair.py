"""One explicit Settings request; radio policy belongs to Rixflix's shared worker."""

import fcntl
import os
import signal
import subprocess
import tempfile
import time

import xbmc
import xbmcgui


WORKER = "/storage/.config/rixflix-remote-pair.py"
STATE = "/storage/.rixflix/remote-pair"
LIMIT = 110


def viewing():
    # Includes paused playback. Settings never interrupts an existing player.
    return xbmc.Player().isPlaying()


def stop(process, monitor):
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait()


def attempt(dialog, monitor):
    if viewing():
        dialog.ok("Pair remote", "Stop playback before pairing your remote.")
        return
    if not os.path.isfile(WORKER):
        dialog.ok("Pair remote", "Remote pairing needs a RixFlix app update. "
                  "The pairing worker is not installed.")
        return
    if not dialog.yesno(
            "Pair remote",
            "Hold Menu + Volume Up on your UR02 until the blue LED blinks slowly. "
            "Then choose Pair now. Keep your TV remote nearby. "
            "This makes one attempt, up to 110 seconds.",
            nolabel="Cancel", yeslabel="Pair now"):
        return
    if viewing() or monitor.abortRequested():
        return
    directory = tempfile.mkdtemp(prefix="attempt-", dir=STATE)
    progress = xbmcgui.DialogProgressBG()
    process = None
    reason = ""
    try:
        progress.create("Pair remote", "Keep the UR02 blue LED blinking. You can still navigate.")
        with open(os.path.join(directory, "pair.log"), "w") as log:
            process = subprocess.Popen(
                ["/usr/bin/python3", WORKER, "--physical-ready"], stdout=log,
                stderr=subprocess.STDOUT, start_new_session=True)
            started = time.monotonic()
            while process.poll() is None:
                elapsed = time.monotonic() - started
                if monitor.abortRequested():
                    reason = "Pairing cancelled because RixFlix is closing."
                    break
                if viewing():
                    reason = "Pairing stopped because playback started. Stop playback and try again."
                    break
                if elapsed >= LIMIT:
                    reason = "Pairing timed out. Check the batteries and try again with the blue LED blinking."
                    break
                progress.update(min(99, int(100 * elapsed / LIMIT)))
                monitor.waitForAbort(0.2)
            if reason:
                stop(process, monitor)
            code = process.wait()
        with open(os.path.join(directory, "exit-code"), "w") as handle:
            handle.write(str(code) + "\n")
        if not reason and code == 0:
            reason = "UR02 connected. Bluetooth pairing, bond, trust, wake and both keyboard and mouse inputs verified."
        elif not reason and code == 75:
            reason = "Another remote pairing attempt is running. Wait for it to finish before trying again."
        elif not reason and code == 3:
            reason = "Playback is active or its state is unknown. Stop playback before pairing."
        elif not reason:
            reason = "UR02 did not fully connect. Hold Back + Menu until one long red flash, " \
                     "then Menu + Volume Up until blue blinks slowly. Choose Pair remote again."
        if code != 0:
            reason += "\nDetails: " + os.path.join(directory, "pair.log")
    except OSError as error:
        reason = "Remote pairing could not start. Try an app update."
        xbmc.log("RixFlix remote pairing: %s" % error, xbmc.LOGERROR)
    finally:
        if process is not None:
            stop(process, monitor)
        progress.close()
    if not monitor.abortRequested():
        dialog.ok("Pair remote", reason)


def main():
    dialog = xbmcgui.Dialog()
    try:
        os.makedirs(STATE, mode=0o700, exist_ok=True)
        # Serialize the physical-ready dialog as well as the worker invocation.
        with open(os.path.join(STATE, "settings.lock"), "a") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                dialog.notification("Pair remote", "A pairing request is already open.")
                return
            attempt(dialog, xbmc.Monitor())
    except OSError as error:
        xbmc.log("RixFlix remote pairing: %s" % error, xbmc.LOGERROR)
        dialog.ok("Pair remote", "Cannot save pairing evidence. Check the app storage and try again.")


if __name__ == "__main__":
    main()
