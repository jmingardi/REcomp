"""Private playable QA session, with real SDL input and owned-window UI controls."""
import argparse
import ctypes
from ctypes import wintypes
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import time

from project import ROOT, BUILD, EVIDENCE, config
from smoke import request

ACTIVE = EVIDENCE / "active-qa-session.json"


def session():
    return json.loads(ACTIVE.read_text())


def rpc(command, **params):
    state = session()
    result = request(state["port"], command, **params)
    with (Path(state["output"]) / "interactions.jsonl").open("a", encoding="utf-8") as log:
        log.write(json.dumps({"time": time.time(), "command": command, "params": params, "response": result}) + "\n")
    return result


def hostpad(action, **params):
    encoded = json.dumps({"action": action, **params}, separators=(",", ":")).encode().hex()
    result = rpc("mod_cmd", name="re1.qa.hostpad", args=encoded)
    if result.get("result") != 1:
        raise RuntimeError(result)
    answer = json.loads(result["reply"])
    if "error" in answer:
        raise RuntimeError(answer)
    return answer


def capture(label):
    state = session()
    output = Path(state["output"])
    result = {"frame": rpc("frame"), "pad": rpc("pad_status"),
              "video": rpc("video_info"), "dispatch": rpc("dispatch_stats"),
              "overlays": rpc("overlay_loader_status"), "motion": rpc("frame_gen")}
    result["image"] = rpc("screenshot_file", path=(output / f"{label}.png").as_posix())
    (output / f"{label}.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def owned_window():
    state = session()
    api = ctypes.windll.user32
    api.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    api.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    api.ClientToScreen.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.POINT)]
    api.SetForegroundWindow.argtypes = [wintypes.HWND]
    api.GetForegroundWindow.restype = wintypes.HWND
    api.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    api.IsWindowVisible.argtypes = [wintypes.HWND]
    api.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
    found = []
    callback = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def visit(hwnd, _):
        pid = wintypes.DWORD()
        api.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        rect = wintypes.RECT()
        api.GetClientRect(hwnd, ctypes.byref(rect))
        if pid.value == state["pid"] and rect.right >= 200 and rect.bottom >= 150:
            found.append((bool(api.IsWindowVisible(hwnd)), rect.right * rect.bottom, hwnd))
        return True
    api.EnumWindows(callback(visit), 0)
    if not found:
        raise RuntimeError("No game/launcher window for the QA process")
    hwnd = max(found)[2]
    return api, hwnd


def click(x, y):
    api, hwnd = owned_window()
    position = (int(y) << 16) | (int(x) & 0xffff)
    api.PostMessageW(hwnd, 0x200, 0, position)
    api.PostMessageW(hwnd, 0x201, 1, position)
    time.sleep(0.1)
    api.PostMessageW(hwnd, 0x202, 0, position)


def key(name, down=None, duration=0.15):
    codes = {"Enter": 13, "Escape": 27, "Up": 38, "Down": 40,
             "Left": 37, "Right": 39, "F10": 121, "F11": 122, "Space": 32,
             "Tab": 9, "Backspace": 8}
    vk = codes.get(name, ord(name.upper()) if len(name) == 1 else 0)
    if not vk:
        raise ValueError(f"Unsupported QA key: {name}")
    api, hwnd = owned_window()
    scan = api.MapVirtualKeyW(vk, 0)
    base = 1 | (scan << 16) | ((1 << 24) if name in ("Up", "Down", "Left", "Right") else 0)
    if down is None or down:
        api.PostMessageW(hwnd, 0x100, vk, base)
    if down is None:
        time.sleep(duration)
    if down is None or not down:
        api.PostMessageW(hwnd, 0x101, vk, base | (1 << 30) | (1 << 31))


def start(launcher=False, route=None, ui_script=None, reuse=None, ignore_real=False, host_route=None, motion=None, capture_burst=0, smooth_60=None):
    output = Path(reuse).resolve() if reuse else EVIDENCE / datetime.now(timezone.utc).strftime("qa-%Y%m%dT%H%M%S%fZ")
    if not output.is_relative_to(EVIDENCE.resolve()) or not output.name.startswith("qa-"):
        raise ValueError("QA output must be a qa-* directory under evidence")
    runtime = output / "runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    source = BUILD / "game/Release"
    for name in ("assets", "bios", "mods/bundled"):
        if (source / name).is_dir():
            shutil.copytree(source / name, runtime / name, dirs_exist_ok=True)
    for name in ("Resident_Evil_Recompiled.exe", "Resident_Evil_Recompiled.execution.json"):
        if (source / name).is_file():
            shutil.copy2(source / name, runtime / name)
    if smooth_60:
        path = runtime / "mods/state.toml"
        text = path.read_text(encoding="utf-8") if path.exists() else "format_version = 2\n"
        prefix = 'package_id = "re1.enhancement.smooth-motion"\nid = "smooth-motion"\nenabled = '
        enabled = "true" if smooth_60 == "on" else "false"
        if prefix in text:
            text = re.sub(re.escape(prefix) + r'(true|false)', lambda _: prefix + enabled, text)
        else:
            text += '\n[[package]]\nid = "re1.enhancement.smooth-motion"\n\n[[feature]]\n' + prefix + enabled + '\n'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    env = dict(os.environ, PSX_DEBUG_SERVER="1", PSX_FRAME_REPORT_MS="5000",
               PSX_OVERLAY_CAPTURE_ROOT=str(output / "overlays"))
    if ui_script:
        env.update(LNG_SCRIPT=ui_script, LNG_TEST_HIDDEN="1")
    if ignore_real:
        # Isolate the detected physical Xbox 360 from virtual-device experiments.
        # This affects only this QA process, never Windows or the user's game.
        env["SDL_GAMECONTROLLER_IGNORE_DEVICES"] = "0x045e/0x028e"
    if motion:
        env.update(PSX_FRAME_GEN="0" if motion == "stock" else "1",
                   PSX_FRAME_GEN_METHOD="redraw" if motion == "stock" else motion,
                   PSX_HOST_REFRESH_HZ="60")
    if capture_burst:
        env["PSX_PRESENT_SHOT_BURST"] = str(capture_burst)
    # The upstream launcher may persist controller defaults into game.toml.
    # Keep that write inside the private profile as well as cards/keybinds.
    private_config = output / "game.toml"
    if not private_config.exists():
        text = (ROOT / "game.toml").read_text(encoding="utf-8")
        for field, relative in (("exe", config()["game"]["exe"]),
                                ("seeds", "seeds/ghidra_funcs.txt"),
                                ("bios_config", "third_party/psxrecomp/bios/OpenBIOS.toml")):
            text = text.replace(f'{field} = "{relative}"',
                                f'{field} = "{(ROOT / relative).as_posix()}"')
        private_config.write_text(text, encoding="utf-8")
    if motion:
        text = private_config.read_text(encoding="utf-8")
        def pipeline(section):
            body = re.sub(r'^render_thread\s*=.*\n?', '', section.group(0), flags=re.MULTILINE)
            return body.replace('[video]\n', '[video]\nrender_thread = true\n', 1)
        text = re.sub(r'(?ms)^\[video\]\n.*?(?=^\[|\Z)', pipeline, text, count=1)
        private_config.write_text(text, encoding="utf-8")
    command = [str(runtime / "Resident_Evil_Recompiled.exe"), "--game", str(private_config),
               "--disc", str(ROOT / config()["game"]["disc"]), "--bios", str(runtime / "bios/openbios.bin"),
               "--memcard-dir", str(output / "saves"), "--debug-port", str(port),
               "--launcher" if launcher else "--no-launcher"]
    if not launcher:
        command.append("--hidden-window")
    with (output / "runtime.log").open("a", encoding="utf-8") as log:
        process = subprocess.Popen(command, cwd=output, env=env, stdout=log, stderr=log,
                                   creationflags=subprocess.CREATE_NO_WINDOW)
        state = {"pid": process.pid, "port": port, "output": str(output), "runtime": str(runtime), "command": command}
        ACTIVE.write_text(json.dumps(state, indent=2))
        (output / "session.json").write_text(json.dumps(state, indent=2))
        (output / f"session-{process.pid}.json").write_text(json.dumps(state, indent=2))
        print(json.dumps(state), flush=True)
        started = time.monotonic()
        timeline = json.loads(Path(route).read_text()) if route else []
        (output / "route.json").write_text(json.dumps(timeline, indent=2))
        next_event = 0
        virtual_ready = False
        release_at = None
        pad_bits = {0: "back", 3: "start", 4: "dpup", 5: "dpright", 6: "dpdown", 7: "dpleft",
                    10: "leftshoulder", 11: "rightshoulder", 12: "y", 13: "b", 14: "a", 15: "x"}
        try:
            while process.poll() is None and time.monotonic() - started < 1500:
                if host_route and not virtual_ready:
                    try:
                        hostpad("attach", profile=host_route)
                        virtual_ready = True
                        print("SDL virtual controller attached", flush=True)
                    except (OSError, RuntimeError):
                        if time.monotonic() - started > 30:
                            raise
                        time.sleep(.2)
                        continue
                if release_at is not None and time.monotonic() >= release_at:
                    hostpad("state")
                    release_at = None
                if next_event < len(timeline) and time.monotonic() - started >= timeline[next_event]["at"]:
                    event = timeline[next_event]
                    capture(f"route-{next_event:02d}-{event.get('label', 'step')}")
                    if "buttons" in event:
                        if host_route:
                            buttons = [name for bit, name in pad_bits.items() if not event["buttons"] & (1 << bit)]
                            hostpad("state", buttons=buttons)
                            release_at = time.monotonic() + event.get("frames", 12) / 60
                            time.sleep(.05)
                            observed = rpc("pad_status")
                            if int(observed["pad"], 16) != event["buttons"] or observed["override"] != -1:
                                raise RuntimeError(f"SDL route did not reach guest pad: {event} {observed}")
                        else:
                            rpc("press", buttons=event["buttons"], frames=event.get("frames", 12), connected=1, pad_type=0)
                    next_event += 1
                    print(f"Route step {next_event}/{len(timeline)}", flush=True)
                time.sleep(0.1)
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
            (output / "exit.json").write_text(json.dumps({"exit_code": process.returncode}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--launcher", action="store_true")
    parser.add_argument("--route", type=Path)
    parser.add_argument("--ui-script", help="Upstream LNG_SCRIPT UI actions/captures")
    parser.add_argument("--reuse", type=Path, help="Restart the same private QA profile to test persistence")
    parser.add_argument("--ignore-real", action="store_true", help="Ignore the detected physical Xbox 360 in this QA process")
    parser.add_argument("--host-route", choices=["xbox", "dualshock", "dualsense", "generic"],
                        help="Drive the route through an SDL virtual controller, without guest input overrides")
    parser.add_argument("--motion", choices=["stock", "redraw", "reprojection"],
                        help="Private render-thread experiment at a simulated 60 Hz host refresh")
    parser.add_argument("--capture-burst", type=int, default=0,
                        help="Capture N full-size real/generated frames per present_shot request (max 240)")
    parser.add_argument("--smooth-60", choices=["on", "off"],
                        help="Set the real 60 FPS Motion mod in the private profile, without experimental env overrides")
    start(**vars(parser.parse_args()))
