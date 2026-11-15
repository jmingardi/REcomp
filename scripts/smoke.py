"""Observe a private hidden native process; screenshots still require visual review."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

from project import ROOT, BUILD, EVIDENCE, config


def request(port, command, **params):
    with socket.create_connection(("127.0.0.1", port), timeout=5) as client:
        client.sendall((json.dumps({"id": 1, "cmd": command, **params}) + "\n").encode())
        data = b""
        while b"\n" not in data:
            block = client.recv(65536)
            if not block:
                break
            data += block
        return json.loads(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=int, default=25)
    parser.add_argument("--renderer", choices=["opengl", "software"], default="opengl")
    parser.add_argument("--press-start", action="store_true", help="Try Start at each sample after the first")
    parser.add_argument("--route", type=Path, help="JSON timeline of pad presses and capture checkpoints")
    args = parser.parse_args()
    if not 5 <= args.seconds <= 300:
        parser.error("--seconds must be between 5 and 300")
    executable = BUILD / "game/Release/Resident_Evil_Recompiled.exe"
    if not executable.exists():
        parser.error("Build the native executable first")
    output = EVIDENCE / datetime.now(timezone.utc).strftime("smoke-%Y%m%dT%H%M%S%fZ")
    output.mkdir(parents=True)
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    env = dict(os.environ, PSX_DEBUG_SERVER="1", PSX_FRAME_REPORT_MS="5000",
               PSX_OVERLAY_CAPTURE_ROOT=str(output / "overlays"))
    command = [str(executable), "--game", str(ROOT / "game.toml"), "--disc",
               str(ROOT / config()["game"]["disc"]), "--bios", str(BUILD / "game/Release/bios/openbios.bin"),
               "--memcard-dir", str(output / "saves"), "--debug-port", str(port),
               "--renderer", args.renderer, "--hidden-window", "--no-launcher"]
    report = {"command": command, "samples": [], "renderer": args.renderer,
              "scope": "Boot observation only; no full-playthrough or fidelity claim"}
    timeline = [{"at": t} for t in (3, max(4, args.seconds // 2), args.seconds)]
    if args.route:
        timeline = json.loads(args.route.read_text(encoding="utf-8")) + [{"at": args.seconds, "label": "final"}]
        if any(not 0 <= event["at"] <= args.seconds for event in timeline):
            parser.error("Route times must be inside the observation interval")
        timeline.sort(key=lambda event: event["at"])
        report["route"] = str(args.route)
        report["route_timeline"] = timeline
        (output / "route.json").write_text(json.dumps(timeline, indent=2) + "\n")
    started = time.monotonic()
    with (output / "runtime.log").open("w", encoding="utf-8") as log:
        process = subprocess.Popen(command, cwd=output, env=env, stdout=log, stderr=log,
                                   creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        report["pid"] = process.pid
        try:
            deadline = started + 20
            while process.poll() is None and time.monotonic() < deadline:
                try:
                    report["connected"] = request(port, "ping")
                    break
                except OSError:
                    time.sleep(0.2)
            if "connected" not in report:
                raise RuntimeError("Native process exited or debug endpoint did not start")
            for index, event in enumerate(timeline):
                target = event["at"]
                while process.poll() is None and time.monotonic() - started < target:
                    time.sleep(0.1)
                if process.poll() is not None:
                    raise RuntimeError(f"Native process exited with {process.returncode}")
                sample = {"elapsed_seconds": round(time.monotonic() - started, 2),
                          "label": event.get("label", str(index))}
                for name in ("frame", "dispatch_stats", "overlay_loader_status", "video_info", "cdrom_state", "get_registers"):
                    sample[name] = request(port, name)
                sample["screenshot"] = request(port, "screenshot_file", path=(output / f"frame-{index}.png").as_posix())
                report["samples"].append(sample)
                print(json.dumps({"elapsed": sample["elapsed_seconds"], "frame": sample["frame"],
                                  "dispatch": sample["dispatch_stats"], "screenshot": sample["screenshot"]}), flush=True)
                if args.press_start or "buttons" in event:
                    # PS1 button words are active-low: Start is bit 3.
                    report.setdefault("inputs", []).append(request(port, "press", buttons=event.get("buttons", 0xFFF7),
                                                                   frames=event.get("frames", 12), connected=1, pad_type=0))
            report["completed_observation"] = True
            frames = [s["frame"].get("frame", 0) for s in report["samples"]]
            report["boot_has_visible_output"] = any(s["screenshot"].get("ok") for s in report["samples"])
            report["frames_advance"] = len(frames) > 1 and frames[-1] > frames[0]
        except (OSError, ValueError, RuntimeError) as error:
            report["error"] = str(error)
        finally:
            if process.poll() is None:
                try:
                    request(port, "quit")
                    process.wait(timeout=5)
                except (OSError, ValueError, subprocess.TimeoutExpired):
                    process.kill()
                    process.wait()
            report["exit_code"] = process.returncode
            (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"Evidence: {output}", flush=True)
    return 0 if (report.get("completed_observation") and report.get("frames_advance")
                 and report.get("boot_has_visible_output")) else 1


if __name__ == "__main__":
    sys.exit(main())
