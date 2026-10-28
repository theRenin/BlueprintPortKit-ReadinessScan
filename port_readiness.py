"""
port_readiness.py: a read-only readiness scan of a project's Blueprints, for BlueprintPortKit.

Run it BEFORE the first port item. It answers "does the kit fit this project, and where do I start?" without opening
the editor and without changing anything. For every Blueprint (also Blueprint structs and enums) under the Content
folders you name it reports:
  - the parent class, the size (variables, functions, bytecode statements, graph nodes) and what depends on it;
  - the constructs on the kit's can't-do list that it contains (SKILL.md, section 6): interfaces, event dispatchers,
    timelines, custom macros, widget property bindings, replication, casts, soft references, whether an Anim
    Blueprint or a State Tree is involved, and the Widget, Anim and Level Blueprints whose reparent is hand work;
  - a bottom-up port order: a Blueprint comes after the Blueprints it needs (cycles are named, not hidden).
The result is one Markdown file (to read) and one JSON file (for tools and agents).

How it reads the project:
  - BlueprintDump (`--list` and `--exports`, see SKILL.md section 7) gives each Blueprint's index and graph nodes.
  - "Who uses it" and the port order come from the package header of every .uasset/.umap file under the Content
    root: the name table lists every asset path the file refers to (parent class, casts, variables, soft
    references, placed actors in levels). BlueprintDump cannot say that, and the header is cheap to read.

Usage:
    python port_readiness.py Content/Characters Content/UI [options]
Options (each can also be a key in a small JSON file given with --settings; the command line wins):
    --dump PATH          BlueprintDump.dll (run with dotnet) or an executable; default: BlueprintDump/BlueprintDump.dll next to this script
    --engine VERSION     engine version that saved the assets: 5.6, 5.7 or 5.8 (default 5.8)
    --content-root PATH  the project's Content folder (default: the nearest folder called Content above the scanned one)
    --mount PATH         the package path the Content root is mounted at (default /Game; a plugin uses /PluginName)
    --out FOLDER         where PortReadiness.md and PortReadiness.json go (default Saved/PortReadiness, made if missing)
    --exclude NAME       folder name to leave out of the Blueprint list, repeatable (they are still searched for references)
    --max-header-mb N    how much of each file's start is searched for references (default 4)
Exit codes: 0 = report written, 1 = error (BlueprintDump missing, bad arguments).

Limits: the scan sees only what is saved on disk. It cannot see level Blueprints, local variables, Call Function By Name
strings or values typed into pins, and the State Tree and Anim Blueprint checks are by file markers, not by member.
"""
import argparse
import datetime
import json
import re
import shutil
import subprocess
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

KIT_DUMP = Path(__file__).resolve().parent / "BlueprintDump" / "BlueprintDump.dll"
# A closing paragraph for the report. Empty here; make_release.py --scan (the free readiness scan package) replaces the next line.
REPORT_FOOTER = 'This report was made by the free BlueprintPortKit Readiness Scan. BlueprintPortKit is the plugin that does the Blueprint side of a Blueprint-to-C++ port for the Blueprints listed above: it re-points every caller of a moved function, deletes what C++ replaced (and refuses while anything still uses it), reparents after a clash check, swaps Blueprint structs, enums and interfaces for their C++ versions, and rebinds State Tree properties. Every tool has a dry run that lists the plan first. More: rgruszkowski@seznam.cz'
DEFAULTS = {
    "folders": [],
    "dump": str(KIT_DUMP),
    "engine": "5.8",
    "content_root": None,
    "mount": "/Game",
    "out": "Saved/PortReadiness",
    "exclude": ["__ExternalActors__", "__ExternalObjects__", "Developers", "Collections"],
    "max_header_mb": 4,
    "workers": 4,
}
FILES_PER_CALL = 25      # files given to one BlueprintDump call (it takes several paths; starting it costs about 0.3 s)
DUMP_TIMEOUT = 600       # seconds for one BlueprintDump call

# The kit's can't-do list, one row per construct: key -> (label, what it means for a port). Edit the text here when
# a kit tool starts to cover a construct; nothing else in this file names a tool.
CONSTRUCTS = {
    "interfaces": ("Interfaces", "`swap_interface` moves the Blueprints that implement a Blueprint Interface onto a C++ interface; message calls in levels and unloaded Blueprints stay a WARNING, and the old interface is deleted by hand"),
    "dispatchers": ("Event dispatchers", "not bridged, renamed or retyped by the kit"),
    "timelines": ("Timelines", "no tool moves a Timeline: its curves and update logic are rewritten in C++ by hand"),
    "macros": ("Custom macros", "logic inside a macro graph is not seen by the call and delete tools"),
    "widget_bindings": ("Widget bindings", "the delete tools refuse while a binding names the member and `rename_member_variable` carries a variable binding along; a bound function in a re-point is a WARNING to bind by hand"),
    "replication": ("Replication", "the reparent preflight compares replication (flag, RepNotify, condition) and the re-point tools the RPC kind; a difference is a WARNING and a real run is refused"),
    "casts": ("Casts", "hand work when the cast target is the class being replaced"),
    "soft_references": ("Soft references", "hand work when the target is the class being replaced"),
    "anim_blueprint": ("Anim Blueprint", "Property Access nodes cannot be edited: the delete tools only warn"),
    "reparent_by_hand": ("Reparent by hand", "`reparent_blueprint` refuses Widget, Animation and Level Blueprints: reparent them in the editor (File > Reparent Blueprint)"),
    "state_tree": ("State Tree", "only plain property bindings are covered; output and completion bindings are hand work"),
}
# What a Blueprint's native root parent says about its kind, when its saved graph does not say it already.
NATIVE_KINDS = {"Interface": "Blueprint Interface", "AnimInstance": "Anim Blueprint",
                "UserWidget": "Widget Blueprint", "BlueprintFunctionLibrary": "Function library",
                "LevelScriptActor": "Level Blueprint"}
# The kinds `reparent_blueprint` refuses (it answers "use the editor's Reparent menu"): the scan lists their reparent as hand work.
REPARENT_BY_HAND_KINDS = ("Widget Blueprint", "Anim Blueprint", "Level Blueprint")
DELEGATE_NODES = {"K2Node_AddDelegate": "bind", "K2Node_AssignDelegate": "assign", "K2Node_CallDelegate": "call",
                  "K2Node_RemoveDelegate": "unbind", "K2Node_ClearDelegate": "clear"}
RPC_FLAGS = {"FUNC_NetServer": "Server RPC", "FUNC_NetClient": "Client RPC", "FUNC_NetMulticast": "Multicast RPC"}
# Words that appear in a package's name table only when the file holds (or points at) a Blueprint, or is a State Tree.
BLUEPRINT_MARKERS = (b"BlueprintGeneratedClass", b"UserDefinedStruct", b"UserDefinedEnum")
STATE_TREE_MARKER = b"StateTreeEditorData"


class ToolError(Exception):
    """A problem the person can fix (a wrong path, a missing BlueprintDump); main() prints it and exits with 1."""


def progress(text):
    """Progress goes to stderr so the files and the final summary line stay clean."""
    print(text, file=sys.stderr)


# ---------------------------------------------------------------- settings

def parse_arguments(argv):
    """The command line. Every option defaults to None so merge_settings can tell 'not given' from a value."""
    parser = argparse.ArgumentParser(description="Read-only readiness scan of a project's Blueprints (BlueprintPortKit).")
    parser.add_argument("folders", nargs="*", help="Content folder(s) to scan")
    parser.add_argument("--settings", help="JSON file with any of the options below as keys")
    parser.add_argument("--dump", help="BlueprintDump.dll or executable")
    parser.add_argument("--engine", help="engine version that saved the assets (5.6, 5.7, 5.8)")
    parser.add_argument("--content-root", dest="content_root", help="the project's Content folder")
    parser.add_argument("--mount", help="package path of the Content root (default /Game)")
    parser.add_argument("--out", help="output folder")
    parser.add_argument("--exclude", action="append", help="folder name to leave out of the list; repeatable")
    parser.add_argument("--max-header-mb", dest="max_header_mb", type=float, help="MB of each file searched for references")
    return parser.parse_args(argv)


def merge_settings(args):
    """Defaults, then the settings file, then the command line. A key the script does not know is an error (typo guard)."""
    settings = dict(DEFAULTS)
    if args.settings:
        try:
            from_file = json.loads(Path(args.settings).read_text(encoding="utf-8"))
        except (OSError, ValueError) as problem:
            raise ToolError(f"cannot read settings file {args.settings}: {problem}")
        unknown = sorted(set(from_file) - set(DEFAULTS))
        if unknown:
            raise ToolError(f"unknown key(s) in {args.settings}: {', '.join(unknown)} (allowed: {', '.join(DEFAULTS)})")
        settings.update(from_file)
    for key in DEFAULTS:
        value = getattr(args, key, None)
        if value:
            settings[key] = value
    if not settings["folders"]:
        raise ToolError("name at least one Content folder to scan, e.g.  python port_readiness.py Content/Characters")
    return settings


def find_content_root(settings):
    """The Content root: given, or the nearest folder called Content at or above the first scanned folder."""
    if settings["content_root"]:
        return Path(settings["content_root"]).resolve()
    first = Path(settings["folders"][0]).resolve()
    for candidate in [first, *first.parents]:
        if candidate.name.lower() == "content":
            return candidate
    return first


# ---------------------------------------------------------------- files and package headers

def list_assets(root):
    """Every .uasset and .umap under the root, sorted, so a run is repeatable."""
    return sorted(p for p in Path(root).rglob("*") if p.suffix.lower() in (".uasset", ".umap"))


def package_path(path, root, mount):
    """The asset's package path as the name table writes it, e.g. /Game/Characters/BP_Hero."""
    relative = Path(path).relative_to(root).with_suffix("")
    return mount.rstrip("/") + "/" + relative.as_posix()


def package_key(path, root, mount):
    """The package path in lower case, used to match and to key dictionaries: Windows file names and the saved names
    can differ in case, and Unreal compares package names without case."""
    return package_path(path, root, mount).lower()


def package_regex(mount):
    """Matches a package path in raw bytes: the mount, then folders and a name. It stops at '.' (an object path
    /Game/X/BP_Hero.BP_Hero_C gives /Game/X/BP_Hero) and at the 0 byte that ends every saved name."""
    return re.compile(re.escape(mount.rstrip("/").encode("ascii")) + rb"(?:/[A-Za-z0-9_+\-]+)+", re.IGNORECASE)


def referenced_packages(data, regex):
    """The package paths in a run of bytes, in lower case."""
    return {found.decode("ascii").lower() for found in regex.findall(data)}


def header_markers(data):
    """'blueprint' when the file holds or points at a Blueprint, struct or enum class; 'state_tree' for a State Tree asset."""
    markers = {"blueprint"} if any(marker in data for marker in BLUEPRINT_MARKERS) else set()
    return markers | ({"state_tree"} if STATE_TREE_MARKER in data else set())


def scan_header(path, cap_bytes, regex):
    """(markers, packages) of one file. The name table sits at the start of the file, so the first few MB are enough;
    reading the whole file would cost gigabytes on a project with big meshes and textures."""
    with open(path, "rb") as stream:
        data = stream.read(cap_bytes)
    return header_markers(data), referenced_packages(data, regex)


# ---------------------------------------------------------------- BlueprintDump

def make_runner(dump, engine):
    """A function (mode, paths) -> BlueprintDump's text. mode is --list or --exports."""
    dump_path = Path(dump)
    if not dump_path.exists():
        raise ToolError(f"BlueprintDump not found at {dump}: pass --dump <path to BlueprintDump.dll>")
    if dump_path.suffix.lower() == ".dll" and not shutil.which("dotnet"):
        raise ToolError("dotnet was not found: install the free .NET 9 runtime from Microsoft")
    start = ["dotnet", str(dump_path)] if dump_path.suffix.lower() == ".dll" else [str(dump_path)]

    def run(mode, paths):
        command = [*start, "--engine", engine, mode, *[str(p) for p in paths]]
        done = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=DUMP_TIMEOUT)
        if done.returncode != 0:                # BlueprintDump exits with 1 for a bad --engine: no file would read, so stop with its message
            raise ToolError(f"BlueprintDump exited with {done.returncode}: {done.stderr.strip()[:300]}")
        return done.stdout
    return run


def split_sections(text):
    """BlueprintDump prints `=== path ===` before each file: {path as given: that file's text}."""
    parts = re.split(r"^=== (.+?) ===$", text, flags=re.M)
    return {parts[i]: parts[i + 1] for i in range(1, len(parts) - 1, 2)}


def dump_chunk(runner, mode, chunk):
    """One BlueprintDump call: ({path: text}, {path: reason}). A file that fails is reported, never dropped silently."""
    try:
        sections = split_sections(runner(mode, chunk))
    except (OSError, subprocess.SubprocessError) as problem:
        return {}, {path: f"BlueprintDump failed: {problem}" for path in chunk}
    texts, failed = {}, {}
    for path in chunk:
        text = sections.get(str(path))
        if text is None:
            failed[path] = "BlueprintDump printed nothing for it"
        elif "failed to load:" in text:
            failed[path] = next(line.strip() for line in text.splitlines() if "failed to load:" in line)
        else:
            texts[path] = text
    return texts, failed


def dump_many(runner, mode, paths, workers):
    """Dump many files in parallel chunks. Returns ({path: text}, {path: reason})."""
    paths = [str(p) for p in paths]
    chunks = [paths[i:i + FILES_PER_CALL] for i in range(0, len(paths), FILES_PER_CALL)]
    texts, failed = {}, {}
    with ThreadPoolExecutor(workers) as pool:
        for done, (chunk_texts, chunk_failed) in enumerate(pool.map(lambda c: dump_chunk(runner, mode, c), chunks), 1):
            texts.update(chunk_texts)
            failed.update(chunk_failed)
            progress(f"  {mode}: {min(done * FILES_PER_CALL, len(paths))}/{len(paths)} files")
    return texts, failed


# ---------------------------------------------------------------- reading BlueprintDump's text

FUNCTION_LINE = re.compile(r"^  (?P<name>[^(]+)\((?P<args>.*?)\)(?: -> \(.*\))?  \[(?P<stmts>\d+) stmts; (?P<flags>[^\]]*)\]$")
VARIABLE_LINE = re.compile(r"^  (?P<name>.+?) : (?P<type>.+?)(?:  \[(?P<tags>[^\]]*)\])?$")
BLOCK_HEADER = re.compile(r"^\[(?P<type>.+?)\] (?P<name>.+?) \(outer: (?P<outer>.*)\)$")
PROPERTY_LINE = re.compile(r"^  (?P<key>\S+) = (?P<value>.*)$")


def parse_list(text):
    """What `BlueprintDump --list` printed for one file: type (blueprint, struct, enum or None), class, parent,
    implemented interfaces, variables, components, functions and, for a struct or enum, how many members it has."""
    listing = {"type": None, "class": None, "parent": None, "implements": [], "variables": [],
               "components": [], "functions": [], "members": 0}
    section = None
    for line in text.splitlines():
        header = re.match(r"^(variables|components|functions) \(\d+\):$", line)
        struct = re.match(r"^struct (.+) \((\d+) fields\):$", line)
        if line.startswith("class: "):
            listing["type"], listing["class"] = "blueprint", line[7:].strip()
        elif line.startswith("parent: "):
            listing["parent"] = line[8:].strip()
        elif line.startswith("implements: "):
            listing["implements"] = [name.strip() for name in line[12:].split(",")]
        elif header:
            section = header.group(1)
        elif struct:
            listing["type"], listing["class"], listing["members"], section = "struct", struct.group(1), int(struct.group(2)), None
        elif re.match(r"^enum .+:$", line):
            listing["type"], section = "enum", "values"
        elif not line.startswith(" "):
            section = None                      # a blank line or "defaults of ...": the section is over
        elif section == "values" and re.match(r"^  \S+ = \d+$", line):
            listing["members"] += 1
        elif section == "variables" and (match := VARIABLE_LINE.match(line)):
            tags = [t.strip() for t in (match["tags"] or "").split(",") if t.strip()]
            listing["variables"].append({"name": match["name"], "type": match["type"], "tags": tags})
        elif section == "components" and (match := VARIABLE_LINE.match(line)):
            listing["components"].append(match["name"])
        elif section == "functions" and (match := FUNCTION_LINE.match(line)):
            flags = [f.strip() for f in match["flags"].split(",")]
            listing["functions"].append({"name": match["name"].strip(), "stmts": int(match["stmts"]), "flags": flags})
    return listing


def parse_exports(text):
    """What `BlueprintDump --exports` printed: a list of blocks {type, name, props}. A graph node is a block like
    `[K2Node_DynamicCast] K2Node_DynamicCast_0 (outer: EventGraph)`, its properties are the indented `Key = value` lines."""
    blocks = []
    for line in text.splitlines():
        header = BLOCK_HEADER.match(line)
        if header:
            blocks.append({"type": header["type"], "name": header["name"], "props": {}})
        elif blocks and (prop := PROPERTY_LINE.match(line)):
            blocks[-1]["props"].setdefault(prop["key"], prop["value"])
    return blocks


# ---------------------------------------------------------------- the can't-do constructs

def field(value, key):
    """One field of a printed struct value: field('{MemberParent=BPI_X_C, MemberName=Hit}', 'MemberName') -> 'Hit'."""
    found = re.search(rf"\b{key}=([^,}}]+)", value or "")
    return found.group(1).strip() if found else "?"


def of_type(blocks, *types):
    """The export blocks of the given types."""
    return [b for b in blocks if b["type"] in types]


def interface_uses(listing, blocks, kind):
    """Implemented Blueprint interfaces (a native C++ interface is no problem), interface-typed variables, interface
    message nodes, and the Blueprint being an interface itself."""
    uses = [f"implements {name}" for name in listing["implements"] if name.endswith("_C")]
    uses += [f"{v['name']}: {v['type']}" for v in listing["variables"] if v["type"].startswith("TScriptInterface<")]
    uses += [f"message {field(b['props'].get('FunctionReference'), 'MemberParent')}.{field(b['props'].get('FunctionReference'), 'MemberName')}"
             for b in of_type(blocks, "K2Node_Message")]
    return uses + (["is a Blueprint Interface"] if kind == "Blueprint Interface" else [])


def dispatcher_uses(listing, blocks):
    """Dispatchers the Blueprint declares, and the bind, call, assign, unbind and clear nodes that use one."""
    uses = [f"declares {v['name']}" for v in listing["variables"] if v["type"].startswith("dispatcher(")]
    return uses + [f"{DELEGATE_NODES[b['type']]} {field(b['props'].get('DelegateReference'), 'MemberName')}"
                   for b in of_type(blocks, *DELEGATE_NODES)]


def timeline_uses(listing, blocks):
    """Timelines: each has a TimelineComponent variable and a Timeline node; the union covers a missing --exports."""
    names = {v["name"] for v in listing["variables"] if v["type"] == "TimelineComponent*"}
    names |= {b["props"]["TimelineName"] for b in of_type(blocks, "K2Node_Timeline") if "TimelineName" in b["props"]}
    return sorted(names)


def macro_uses(blocks):
    """Macros from a project's own macro library. Epic's StandardMacros (ForEachLoop, Gate...) are compiled into the
    graph and cause no trouble, so they are not counted."""
    uses = []
    for node in of_type(blocks, "K2Node_MacroInstance"):
        reference = node["props"].get("MacroGraphReference", "")
        if field(reference, "GraphBlueprint") != "StandardMacros":
            uses.append(f"{field(reference, 'MacroGraph')} ({field(reference, 'GraphBlueprint')})")
    return uses


def widget_binding_uses(blocks):
    """Property bindings of a widget (a Text or Visibility bound to a function): the saved class holds them in `Bindings`.
    The WidgetBlueprint export holds a second copy, so only the generated class is read."""
    uses = []
    for block in blocks:
        if block["type"].endswith("GeneratedClass"):
            uses += [f"{obj}.{prop}" for obj, prop in
                     re.findall(r"ObjectName=([^,}]+), PropertyName=([^,}]+)", block["props"].get("Bindings", ""))]
    return uses


def replication_uses(listing):
    """Replicated variables, RPC functions and RepNotify functions: the reparent preflight does not compare them."""
    uses = [f"{v['name']} replicated" for v in listing["variables"] if "replicated" in v["tags"]]
    for function in listing["functions"]:
        uses += [f"{function['name']} {text}" for flag, text in RPC_FLAGS.items() if flag in function["flags"]]
        if function["name"].startswith("OnRep_"):
            uses.append(f"{function['name']} RepNotify")
    return uses


def tally(names):
    """['A', 'A', 'B'] -> ['A x2', 'B']: a readable list for the report."""
    return [f"{name} x{count}" if count > 1 else name for name, count in sorted(Counter(names).items())]


def find_constructs(listing, blocks, kind):
    """{construct key: {count, items}} for the constructs this Blueprint contains (empty ones left out)."""
    found = {
        "interfaces": interface_uses(listing, blocks, kind),
        "dispatchers": dispatcher_uses(listing, blocks),
        "timelines": timeline_uses(listing, blocks),
        "macros": macro_uses(blocks),
        "widget_bindings": widget_binding_uses(blocks),
        "replication": replication_uses(listing),
        "casts": [f"cast to {b['props'].get('TargetType', '?')}" for b in of_type(blocks, "K2Node_DynamicCast")],
        "soft_references": [f"{v['name']}: {v['type']}" for v in listing["variables"]
                            if v["type"].startswith(("TSoftObjectPtr<", "TSoftClassPtr<"))],
    }
    if kind in REPARENT_BY_HAND_KINDS:
        found["reparent_by_hand"] = [kind]
    return {key: {"count": len(uses), "items": tally(uses)} for key, uses in found.items() if uses}


# ---------------------------------------------------------------- one entry per Blueprint

def blueprint_kind(listing, blocks, native_root):
    """Struct, Enum, Anim Blueprint, Widget Blueprint... from the saved class (best) or the native root parent."""
    if listing["type"] != "blueprint":
        return listing["type"].capitalize()
    class_types = {b["type"] for b in blocks if b["type"].endswith("GeneratedClass")}
    if "AnimBlueprintGeneratedClass" in class_types:
        return "Anim Blueprint"
    if "WidgetBlueprintGeneratedClass" in class_types:
        return "Widget Blueprint"
    return NATIVE_KINDS.get(native_root, "Blueprint")


def native_root_of(listing, by_class):
    """Follow the parent chain through scanned Blueprints (a name ending in _C) to the first native class."""
    seen, parent = set(), listing["parent"]
    while parent in by_class and parent not in seen:
        seen.add(parent)
        parent = by_class[parent]["parent"]
    return parent


def size_of(listing, blocks):
    """How big the Blueprint is: variables and functions (without the engine's own helpers), bytecode statements, graph nodes."""
    return {
        "variables": sum(1 for v in listing["variables"] if v["name"] != "UberGraphFrame"),
        "components": len(listing["components"]),
        "functions": sum(1 for f in listing["functions"] if not f["name"].startswith("ExecuteUbergraph")),
        "statements": sum(f["stmts"] for f in listing["functions"]),
        "nodes": sum(1 for b in blocks if b["type"].startswith("K2Node_")),
        "members": listing["members"],
    }


def build_entries(root, mount, listings, exports):
    """One entry per readable Blueprint, struct or enum, keyed by its lower-case package path."""
    by_class = {l["class"]: l for l in listings.values()}
    entries = {}
    for path, listing in listings.items():
        blocks = parse_exports(exports.get(path, ""))
        native_root = native_root_of(listing, by_class) if listing["type"] == "blueprint" else None
        kind = blueprint_kind(listing, blocks, native_root)
        entries[package_key(path, root, mount)] = {
            "name": Path(path).stem, "package": package_path(path, root, mount), "file": Path(path).relative_to(root).as_posix(), "kind": kind,
            "parent": listing["parent"], "native_root": native_root, "implements": listing["implements"],
            "size": size_of(listing, blocks), "constructs": find_constructs(listing, blocks, kind),
            "depends_on": [], "referenced_by": {}, "wave": 0, "cycle": None, "order": 0,
        }
    return entries


# ---------------------------------------------------------------- who uses it, and the port order

def classify_referrer(path, markers, root, entries, mount):
    """Which list a referring file goes into, as (bucket, display name)."""
    key = package_key(path, root, mount)
    if key in entries:
        return "blueprints", entries[key]["name"]
    if Path(path).suffix.lower() == ".umap":
        return "levels", Path(path).stem
    if "__ExternalActors__" in Path(path).relative_to(root).parts:
        return "placed_actors", Path(path).stem
    if "state_tree" in markers:
        return "state_trees", Path(path).stem
    return "other", Path(path).stem


def attach_references(entries, hits, root, mount):
    """Fill referenced_by and depends_on from the header scan; returns deps = {package: set of packages it needs}.
    hits = {file: (markers, the Blueprint packages the file refers to)}. A file that refers to a package depends on it
    (the Blueprint's parent, a cast target, a variable type...). A placed actor in a level counts only as a number:
    there can be thousands."""
    for entry in entries.values():
        entry["referenced_by"] = {"blueprints": [], "levels": [], "state_trees": [], "other": [], "placed_actors": 0}
    deps = {key: set() for key in entries}
    for path, (markers, packages) in sorted(hits.items(), key=lambda item: str(item[0])):
        bucket, name = classify_referrer(path, markers, root, entries, mount)
        own = package_key(path, root, mount)
        for package in sorted(packages - {own}):
            used = entries[package]["referenced_by"]
            if bucket == "placed_actors":
                used["placed_actors"] += 1
            else:
                used[bucket].append(name)
            if bucket == "blueprints":
                deps[own].add(package)
    for key, needed in deps.items():
        entries[key]["depends_on"] = sorted(entries[k]["name"] for k in needed)
    return deps


def add_reference_constructs(entries):
    """Anim Blueprints and State Trees show up as constructs of the Blueprints they use (their bindings and Property
    Access nodes name the members); an Anim Blueprint is a construct of its own."""
    kinds = {e["name"]: e["kind"] for e in entries.values()}
    for entry in entries.values():
        anim = [f"used by {name}" for name in entry["referenced_by"]["blueprints"] if kinds.get(name) == "Anim Blueprint"]
        anim += ["is an Anim Blueprint"] if entry["kind"] == "Anim Blueprint" else []
        trees = [f"used by {name}" for name in entry["referenced_by"]["state_trees"]]
        for key, uses in (("anim_blueprint", anim), ("state_tree", trees)):
            if uses:
                entry["constructs"][key] = {"count": len(uses), "items": tally(uses)}


def strongly_connected_groups(deps):
    """Tarjan's algorithm without recursion (a long chain of Blueprints would exceed Python's recursion limit).
    deps = {node: set of nodes it needs}. Returns the groups with the needed ones first: a group of one is a plain
    Blueprint, a bigger group is a cycle of Blueprints that refer to each other."""
    index, low, on_stack, stack, groups = {}, {}, set(), [], []

    def enter(node, work):
        index[node] = low[node] = len(index)
        stack.append(node)
        on_stack.add(node)
        work.append((node, iter(sorted(deps[node]))))

    for root in sorted(deps):
        if root in index:
            continue
        work = []
        enter(root, work)
        while work:
            node, children = work[-1]
            descended = False
            for child in children:
                if child not in index:
                    enter(child, work)
                    descended = True
                    break
                if child in on_stack:
                    low[node] = min(low[node], index[child])
            if descended:
                continue
            work.pop()
            if work:
                low[work[-1][0]] = min(low[work[-1][0]], low[node])
            if low[node] == index[node]:
                group = []
                while not group or group[-1] != node:
                    group.append(stack.pop())
                    on_stack.discard(group[-1])
                groups.append(sorted(group))
    return groups


def port_order(deps):
    """({node: wave}, [cycles]). Wave 0 needs no other Blueprint of the project; every other node sits one wave
    after the latest wave it needs. The members of a cycle share a wave: port them together."""
    groups = strongly_connected_groups(deps)
    group_of = {node: number for number, group in enumerate(groups) for node in group}
    group_wave = []
    for number, group in enumerate(groups):
        needed = {group_of[d] for node in group for d in deps[node]} - {number}
        group_wave.append(1 + max(group_wave[g] for g in needed) if needed else 0)
    return {node: group_wave[group_of[node]] for node in deps}, [g for g in groups if len(g) > 1]


def apply_order(entries, deps):
    """Set wave, cycle and order on every entry and return (waves as lists of names, cycles as lists of names)."""
    wave_of, cycles = port_order(deps)
    for number, group in enumerate(cycles, 1):
        for key in group:
            entries[key]["cycle"] = f"C{number}"
    ranked = [e for _, e in sorted(entries.items(), key=lambda item: (wave_of[item[0]], item[1]["name"].lower()))]
    for rank, entry in enumerate(ranked, 1):
        entry["order"] = rank
    for key, entry in entries.items():
        entry["wave"] = wave_of[key]
    waves = [[e["name"] for e in ranked if e["wave"] == w] for w in range(max(wave_of.values(), default=-1) + 1)]
    return waves, [[entries[k]["name"] for k in group] for group in cycles]


# ---------------------------------------------------------------- the scan

def scan(settings, runner, today=None):
    """Run the whole scan and return the report (a dict that write_reports turns into the two files)."""
    root = find_content_root(settings)
    folders = [Path(f).resolve() for f in settings["folders"]]
    for folder in folders:
        if not folder.is_dir() or root not in [folder, *folder.parents]:
            raise ToolError(f"{folder} is not a folder inside the Content root {root} (use --content-root)")
    regex, cap = package_regex(settings["mount"]), int(settings["max_header_mb"] * 1024 * 1024)
    excluded = set(settings["exclude"])
    all_files = list_assets(root)
    in_scope = [f for f in all_files if f.suffix.lower() == ".uasset" and any(d in f.parents for d in folders)
                and not excluded & set(f.relative_to(root).parts)]
    progress(f"{len(in_scope)} assets in the scanned folders, {len(all_files)} files under {root}")

    with ThreadPoolExecutor(settings["workers"]) as pool:
        first_pass = dict(zip(in_scope, pool.map(lambda f: scan_header(f, cap, regex), in_scope)))
        candidates = [f for f, (markers, _) in first_pass.items() if "blueprint" in markers]
        listing_texts, failed = dump_many(runner, "--list", candidates, settings["workers"])
        listings = {Path(p): parse_list(t) for p, t in listing_texts.items()}
        listings = {p: l for p, l in listings.items() if l["type"]}     # a Data Table that merely points at a Blueprint is no Blueprint
        blueprint_files = [p for p, l in listings.items() if l["type"] == "blueprint"]
        export_texts, export_failed = dump_many(runner, "--exports", blueprint_files, settings["workers"])
        entries = build_entries(root, settings["mount"], listings, {Path(p): t for p, t in export_texts.items()})
        failed.update({p: f"graph nodes not read: {reason}" for p, reason in export_failed.items()})

        # Second pass: the files outside the scanned folders (levels, placed actors, other assets) can use a Blueprint too.
        wanted = set(entries)
        hits = {f: (m, p & wanted) for f, (m, p) in first_pass.items() if p & wanted}
        rest = [f for f in all_files if f not in first_pass]
        for f, (markers, packages) in zip(rest, pool.map(lambda f: scan_header(f, cap, regex), rest)):
            if packages & wanted:
                hits[f] = (markers, packages & wanted)
    deps = attach_references(entries, hits, root, settings["mount"])
    add_reference_constructs(entries)
    waves, cycles = apply_order(entries, deps)
    return make_report(settings, root, entries, waves, cycles, failed, today)


def make_report(settings, root, entries, waves, cycles, failed, today):
    """The report dict: settings used, a summary, one row per construct, every entry in port order, waves, cycles."""
    ordered = sorted(entries.values(), key=lambda e: e["order"])
    constructs = {}
    for key, (label, note) in CONSTRUCTS.items():
        with_it = [e for e in ordered if key in e["constructs"]]
        constructs[key] = {"label": label, "note": note, "blueprints": len(with_it),
                           "occurrences": sum(e["constructs"][key]["count"] for e in with_it)}
    clear = sum(1 for e in ordered if not e["constructs"])
    return {
        "generated": (today or datetime.date.today()).isoformat(),
        "settings": {"folders": [str(f) for f in settings["folders"]], "content_root": str(root), "mount": settings["mount"],
                     "engine": settings["engine"], "exclude": settings["exclude"]},
        "summary": {"entries": len(ordered), "blueprints": sum(1 for e in ordered if e["kind"] not in ("Struct", "Enum")),
                    "structs": sum(1 for e in ordered if e["kind"] == "Struct"), "enums": sum(1 for e in ordered if e["kind"] == "Enum"),
                    "without_hand_work": clear, "with_hand_work": len(ordered) - clear, "cycles": len(cycles), "unreadable": len(failed)},
        "constructs": constructs, "blueprints": ordered, "waves": waves, "cycles": cycles,
        "unreadable": [{"file": str(p), "reason": r} for p, r in sorted(failed.items())],
    }


# ---------------------------------------------------------------- the two files

def hand_work_text(entry):
    """'3 casts, 1 timeline' style short text for the table."""
    return ", ".join(f"{CONSTRUCTS[k][0].lower()} {v['count']}" for k, v in entry["constructs"].items()) or "none"


def portable_lines(report, cap=40):
    """The Blueprints (not structs or enums) with none of the hand-work constructs, in port order: what the kit's tools can move without
    your help. At most `cap` names; the JSON file has every entry."""
    names = [e["name"] for e in report["blueprints"] if not e["constructs"] and e["kind"] not in ("Struct", "Enum")]
    if not names:
        return ["None of the Blueprints is free of the constructs below: every one needs some hand work."]
    shown = ", ".join(names[:cap]) + (f" ... and {len(names) - cap} more" if len(names) > cap else "")
    return [f"{len(names)} Blueprint(s), in port order: {shown}"]


def markdown_lines(report):
    """The Markdown report, as a list of lines."""
    s, settings = report["summary"], report["settings"]
    lines = [f"# Port readiness: {', '.join(Path(f).name for f in settings['folders'])}", "",
             f"Generated {report['generated']} by `port_readiness.py` (read-only, from the saved files). Content root `{settings['content_root']}`, "
             f"mounted at `{settings['mount']}`, saved by UE {settings['engine']}.", "",
             "## Summary", "",
             f"- {s['blueprints']} Blueprints, {s['structs']} structs, {s['enums']} enums.",
             f"- {s['without_hand_work']} have none of the constructs below; {s['with_hand_work']} contain at least one (hand work).",
             f"- {s['cycles']} cycle(s) of Blueprints that refer to each other; {s['unreadable']} file(s) BlueprintDump could not read.", "",
             "## Can be ported with the kit alone", ""]
    lines += portable_lines(report)
    lines += ["", "## What the kit cannot do, found in this project", "",
             "| Construct | Blueprints | Occurrences | What it means |", "|---|---|---|---|"]
    lines += [f"| {c['label']} | {c['blueprints']} | {c['occurrences']} | {c['note']} |" for c in report["constructs"].values()]
    lines += ["", "## Port order (bottom-up)", "",
              "A Blueprint comes after the Blueprints it needs. Everything in one wave can be ported in any order; wave 0 needs no other Blueprint of the project.", ""]
    lines += [f"- Wave {number}: {', '.join(names)}" for number, names in enumerate(report["waves"])]
    for number, group in enumerate(report["cycles"], 1):
        lines.append(f"- Cycle C{number}: {', '.join(group)} refer to each other; port them in one item or break the cycle first.")
    lines += ["", "## Blueprints", "", "| # | Blueprint | Kind | Parent | Statements | Needs | Used by | Hand work |", "|---|---|---|---|---|---|---|---|"]
    for e in report["blueprints"]:
        used = e["referenced_by"]
        used_by = len(used["blueprints"]) + len(used["levels"]) + len(used["state_trees"]) + len(used["other"]) + used["placed_actors"]
        lines.append(f"| {e['order']} | {e['name']} | {e['kind']} | {e['parent'] or ''} | {e['size']['statements']} | "
                     f"{len(e['depends_on'])} | {used_by} | {hand_work_text(e)} |")
    lines += ["", "## Hand work in detail", ""]
    for e in report["blueprints"]:
        for key, found in e["constructs"].items():
            lines.append(f"- **{e['name']}**, {CONSTRUCTS[key][0].lower()}: {'; '.join(found['items'][:8])}" + (" ..." if len(found["items"]) > 8 else ""))
    if report["unreadable"]:
        lines += ["", "## Not read", ""] + [f"- `{u['file']}`: {u['reason']}" for u in report["unreadable"]]
    if REPORT_FOOTER:
        lines += ["", "---", "", REPORT_FOOTER]
    return lines + [""]


def write_reports(report, out_folder):
    """Write PortReadiness.md and PortReadiness.json; returns their paths."""
    folder = Path(out_folder)
    folder.mkdir(parents=True, exist_ok=True)
    md, js = folder / "PortReadiness.md", folder / "PortReadiness.json"
    md.write_text("\n".join(markdown_lines(report)), encoding="utf-8")
    js.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    return md, js


def main(argv=None):
    """The command line. Prints one summary line and the two file paths; errors go to stderr with exit code 1."""
    try:
        settings = merge_settings(parse_arguments(argv))
        report = scan(settings, make_runner(settings["dump"], settings["engine"]))
        md, js = write_reports(report, settings["out"])
    except ToolError as problem:
        print(f"error: {problem}", file=sys.stderr)
        return 1
    s = report["summary"]
    print(f"{s['entries']} entries, {s['with_hand_work']} with hand work, {s['cycles']} cycle(s), {s['unreadable']} unreadable")
    print(md)
    print(js)
    return 0


if __name__ == "__main__":
    sys.exit(main())
