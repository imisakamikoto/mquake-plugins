#!/usr/bin/env python3
"""mqe —— Mquake 插件开发命令行工具（仅用 Python 标准库，无需安装依赖）。

用法：
    python mqe.py new <id> [目录]        生成插件脚手架
    python mqe.py validate <路径>        校验目录或 .mqe 包
    python mqe.py pack <目录> [输出.mqe] 打包成 .mqe
    python mqe.py unpack <包.mqe> [目录] 解包到目录
    python mqe.py info <包.mqe>          打印清单摘要

退出码：0 成功，1 校验/参数错误，2 IO 错误。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import zipfile
from pathlib import Path

SCHEMA_VERSION = 1
MANIFEST = "plugin.json"
EXT = ".mqe"
MAX_UNPACKED = 32 * 1024 * 1024
MAX_FILE = 8 * 1024 * 1024
MAX_ENTRIES = 512
MIN_INTERVAL = 5

CAPABILITIES = {
    "events", "stations", "overlay", "cards", "metrics", "tiles",
    "sounds", "theme", "actions", "rules", "webhook", "notifications",
}
TRANSPORTS = {"file", "http", "websocket", "process"}
SETTING_TYPES = {"text", "number", "toggle", "select"}
ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{1,63}$")


class Validation:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def err(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    @property
    def ok(self) -> bool:
        return not self.errors


def unsafe_path(p: str) -> bool:
    n = p.replace("\\", "/")
    if n.startswith("/") or re.match(r"^[A-Za-z]:", n):
        return True
    return ".." in n.split("/")


def host_allowed(host: str, allow: list[str]) -> bool:
    h = host.lower()
    for e in allow:
        e = str(e).strip().lower()
        if not e:
            continue
        if e == h:
            return True
        if e.startswith("*.") and h.endswith(e[1:]):
            return True
    return False


def validate_manifest(data: object) -> Validation:
    v = Validation()
    if not isinstance(data, dict):
        v.err("plugin.json 顶层必须是对象")
        return v
    m = data
    if m.get("schema") != SCHEMA_VERSION:
        v.err(f"schema 必须为 {SCHEMA_VERSION}（当前 {m.get('schema')!r}）")
    pid = str(m.get("id", ""))
    if not ID_RE.match(pid):
        v.err("id 非法：只允许小写字母/数字/点/下划线/连字符，长度 2-64，字母数字开头")
    if not str(m.get("name", "")).strip():
        v.err("name 不能为空")
    if not re.match(r"^\d+\.\d+\.\d+", str(m.get("version", ""))):
        v.warn("version 建议用语义化版本 x.y.z")
    caps = m.get("capabilities", [])
    if not isinstance(caps, list) or not caps:
        v.warn("capabilities 为空，插件不会产生任何数据")
    else:
        for c in caps:
            if c not in CAPABILITIES:
                v.err(f"未知能力 {c!r}；可用：{', '.join(sorted(CAPABILITIES))}")

    perms = m.get("permissions", {}) or {}
    if not isinstance(perms, dict):
        v.err("permissions 必须是对象")
        perms = {}
    hosts = perms.get("hosts", []) or []
    if not isinstance(hosts, list):
        v.err("permissions.hosts 必须是字符串数组")
        hosts = []

    t = m.get("transport", {}) or {}
    if not isinstance(t, dict):
        v.err("transport 必须是对象")
        return v
    kind = str(t.get("type", "file"))
    if kind not in TRANSPORTS:
        v.err(f"未知通道类型 {kind!r}；可用：{', '.join(sorted(TRANSPORTS))}")
    if kind == "file":
        f = str(t.get("file", ""))
        if not f:
            v.err("transport.type=file 必须提供 transport.file")
        elif unsafe_path(f):
            v.err("transport.file 路径不安全（绝对路径或 ..）")
    elif kind in ("http", "websocket"):
        url = str(t.get("url", ""))
        from urllib.parse import urlparse
        u = urlparse(url)
        if not u.scheme or not u.hostname:
            v.err(f"transport.url 不是合法 URL：{url!r}")
        elif u.scheme not in ("http", "https", "ws", "wss"):
            v.err("transport.url 只支持 http/https/ws/wss")
        elif not host_allowed(u.hostname, hosts):
            v.err(f"主机 {u.hostname} 不在 permissions.hosts 白名单内")
    elif kind == "process":
        if not str(t.get("command", "")).strip():
            v.err("transport.type=process 必须提供 transport.command")
        if not perms.get("process"):
            v.err("使用 process 通道必须显式设置 permissions.process=true")
        if unsafe_path(str(t.get("command", ""))):
            v.err("transport.command 路径不安全")

    interval = t.get("intervalSeconds", 60)
    if isinstance(interval, (int, float)) and interval < MIN_INTERVAL:
        v.warn(f"intervalSeconds 低于 {MIN_INTERVAL}s，运行时会按下限执行")

    if "overlay" in caps and not perms.get("overlay"):
        v.warn("声明 overlay 但未授予 permissions.overlay，地图数据会被忽略")
    if "sounds" in caps and not perms.get("sound"):
        v.warn("声明 sounds 但未授予 permissions.sound，音效不会被替换")
    if "webhook" in caps:
        v.warn("webhook 会向外部发送数据，请确认 permissions.hosts 已限制目标主机")

    settings = m.get("settings", []) or []
    if not isinstance(settings, list):
        v.err("settings 必须是数组")
    else:
        keys: set[str] = set()
        for s in settings:
            if not isinstance(s, dict):
                v.err("settings 条目必须是对象")
                continue
            key = str(s.get("key", ""))
            if not key or key in keys:
                v.err(f"settings 存在空 key 或重复 key：{key!r}")
            keys.add(key)
            st = str(s.get("type", "text"))
            if st not in SETTING_TYPES:
                v.err(f"settings[{key}].type 未知：{st!r}")
            if st == "select" and not s.get("options"):
                v.err(f"settings[{key}] 是 select 但缺少 options")
    return v


def read_manifest_from_dir(path: Path) -> tuple[dict, Validation]:
    f = path / MANIFEST
    if not f.is_file():
        v = Validation()
        v.err(f"缺少 {MANIFEST}")
        return {}, v
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
        v = Validation()
        v.err(f"{MANIFEST} 解析失败：{e}")
        return {}, v
    return data, validate_manifest(data)


def iter_source_files(path: Path):
    skip_dirs = {".git", "__pycache__", "node_modules", ".idea", ".vscode"}
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith(".")]
        for name in files:
            if name.startswith(".") or name.endswith(EXT):
                continue
            full = Path(root) / name
            rel = full.relative_to(path).as_posix()
            yield rel, full


def pack(src: Path, out: Path | None = None) -> Path:
    if not src.is_dir():
        raise ValueError(f"不是目录：{src}")
    data, v = read_manifest_from_dir(src)
    _print_validation(v)
    if not v.ok:
        raise ValueError("清单校验失败，拒绝打包")
    out = out or (src.parent / f"{data['id']}{EXT}")
    if out.is_dir():
        out = out / f"{data['id']}{EXT}"
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for rel, full in iter_source_files(src):
            z.write(full, rel)
    print(f"[OK] 已打包 {out}（{out.stat().st_size} 字节）")
    return out


def inspect_package(path: Path) -> dict:
    if not path.is_file():
        raise ValueError(f"不是文件：{path}")
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        if len(names) > MAX_ENTRIES:
            raise ValueError(f"包内文件数超过 {MAX_ENTRIES}")
        if MANIFEST not in names:
            raise ValueError(f"包根目录缺少 {MANIFEST}")
        total = 0
        for info in z.infolist():
            n = info.filename.replace("\\", "/")
            if n.startswith("/") or re.match(r"^[A-Za-z]:", n) or ".." in n.split("/"):
                raise ValueError(f"包内存在不安全路径：{info.filename}")
            if info.file_size > MAX_FILE:
                raise ValueError(f"单文件过大：{n}")
            total += info.file_size
            if total > MAX_UNPACKED:
                raise ValueError("解压后总体积超过上限（防 zip 炸弹）")
        raw = z.read(MANIFEST)
        return json.loads(raw.decode("utf-8"))


def unpack(path: Path, dest: Path | None = None) -> Path:
    data = inspect_package(path)
    dest = dest or (path.parent / data["id"])
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path) as z:
        for info in z.infolist():
            n = info.filename.replace("\\", "/")
            if n.startswith("/") or ".." in n.split("/"):
                raise ValueError(f"拒绝不安全路径：{info.filename}")
        z.extractall(dest)
    print(f"[OK] 已解包到 {dest}")
    return dest


def _print_validation(v: Validation) -> None:
    for w in v.warnings:
        print(f"[WARN] {w}")
    for e in v.errors:
        print(f"[ERROR] {e}")


def cmd_new(plugin_id: str, dest: Path) -> None:
    if not ID_RE.match(plugin_id):
        raise ValueError(f"插件 id 非法：{plugin_id!r}")
    dest.mkdir(parents=True, exist_ok=True)
    if (dest / MANIFEST).exists():
        raise ValueError(f"目标目录已有 {MANIFEST}：{dest}")
    manifest = {
        "schema": SCHEMA_VERSION,
        "id": plugin_id,
        "name": plugin_id,
        "version": "1.0.0",
        "author": "",
        "description": "我的第一个 Mquake 插件",
        "capabilities": ["cards", "metrics"],
        "permissions": {"hosts": [], "process": False, "alerts": False,
                        "sound": False, "overlay": False},
        "transport": {"type": "file", "file": "data.json", "intervalSeconds": 60},
        "settings": [
            {"key": "city", "label": "城市", "type": "text", "default": "Tokyo"}
        ],
    }
    (dest / MANIFEST).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    data = {
        "type": "snapshot",
        "cards": [{"id": "hello", "title": "Hello, Mquake!",
                   "body": "这是来自插件的信息卡。",
                   "rows": [{"label": "城市", "value": "Tokyo"}]}],
        "metrics": [{"id": "demo", "label": "示例指标", "value": 42,
                     "unit": "", "history": [38, 39, 41, 40, 42]}],
    }
    (dest / "data.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (dest / "README.md").write_text(
        f"# {plugin_id}\n\n用 `python mqe.py pack {dest.name}` 打包为 "
        f"`{plugin_id}.mqe`，然后在应用「设置 → 插件」里安装。\n",
        encoding="utf-8",
    )
    print(f"[OK] 脚手架已生成：{dest}")


def cmd_info(path: Path) -> None:
    data = inspect_package(path)
    print(f"id          : {data.get('id')}")
    print(f"name        : {data.get('name')}")
    print(f"version     : {data.get('version')}")
    print(f"schema      : {data.get('schema')}")
    print(f"capabilities: {', '.join(data.get('capabilities', [])) or '(无)'}")
    t = data.get("transport", {})
    print(f"transport   : {t.get('type')} -> {t.get('file') or t.get('url') or t.get('command')}")
    with zipfile.ZipFile(path) as z:
        print(f"files       : {len(z.namelist())}")
        for n in z.namelist():
            print(f"  - {n}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="mqe", description="Mquake 插件 (.mqe) 开发套件",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("new", help="生成插件脚手架")
    p.add_argument("id")
    p.add_argument("dir", nargs="?", default=None)

    p = sub.add_parser("validate", help="校验目录或 .mqe")
    p.add_argument("path")

    p = sub.add_parser("pack", help="打包目录为 .mqe")
    p.add_argument("dir")
    p.add_argument("out", nargs="?", default=None)

    p = sub.add_parser("unpack", help="解包 .mqe")
    p.add_argument("file")
    p.add_argument("dir", nargs="?", default=None)

    p = sub.add_parser("info", help="查看 .mqe 摘要")
    p.add_argument("file")

    args = ap.parse_args(argv)
    try:
        if args.cmd == "new":
            cmd_new(args.id, Path(args.dir) if args.dir else Path(args.id))
        elif args.cmd == "validate":
            target = Path(args.path)
            if target.is_dir():
                _, v = read_manifest_from_dir(target)
                # 顺带检查数据文件是否可读
                data, _ = read_manifest_from_dir(target)
                f = (data.get("transport") or {}).get("file")
                if f:
                    fp = target / str(f)
                    if not fp.is_file():
                        v.err(f"找不到 transport.file：{f}")
                    else:
                        try:
                            json.loads(fp.read_text(encoding="utf-8"))
                        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
                            v.err(f"{f} 不是合法 JSON：{e}")
            else:
                data = inspect_package(target)
                _, v = (data, validate_manifest(data))
            _print_validation(v)
            print("[OK] 校验通过" if v.ok else "[FAIL] 校验未通过")
            return 0 if v.ok else 1
        elif args.cmd == "pack":
            pack(Path(args.dir), Path(args.out) if args.out else None)
        elif args.cmd == "unpack":
            unpack(Path(args.file), Path(args.dir) if args.dir else None)
        elif args.cmd == "info":
            cmd_info(Path(args.file))
        return 0
    except (ValueError, OSError, zipfile.BadZipFile, json.JSONDecodeError) as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
