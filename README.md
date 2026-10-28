# BlueprintPortKit Readiness Scan

A free scan that tells you how ready your Unreal Engine project is for a Blueprint-to-C++ port.

It reads the Blueprints saved in your Content folders and reports:

- which Blueprints can be ported with the BlueprintPortKit tools alone,
- what the tools handle and check in their dry run: interfaces, event dispatchers, widget bindings, replication, State Tree bindings, casts and soft references (each row says what stays by hand),
- what stays hand work: timelines, custom macros, Anim Blueprint property access, and Widget/Anim/Level Blueprints that must be reparented in the editor,
- the order to port in: a Blueprint comes after the Blueprints it needs, and cycles are named.

Read-only. No editor needed. It changes nothing and does not use the network.

## Run

You need Windows, Python 3 and the free [.NET 9 runtime](https://dotnet.microsoft.com/download/dotnet/9.0) (or a newer one). Assets saved by Unreal Engine 5.6, 5.7 or 5.8.

```
python port_readiness.py "<YourProject>/Content/Characters" "<YourProject>/Content/UI" --engine 5.8
```

Name the Content folders you want scanned (the whole `Content` folder works too). `--engine` is the version that saved the assets. `python port_readiness.py --help` lists every option.

## What you get

- `Saved/PortReadiness/PortReadiness.md`: read this. A summary, the Blueprints that can be ported with the kit alone, the hand work found, the port order and one row per Blueprint.
- `Saved/PortReadiness/PortReadiness.json`: the same for a script or a coding agent.

`--out FOLDER` puts them somewhere else.

## Sample reports

The scan run (read-only) on Epic Games' Unreal Engine 5.8 Blueprint templates, each base template with one of its variants:

| Template | Blueprints | Can be ported with the kit alone | Report |
|---|---|---|---|
| Third Person + Combat | 37 | 32 | [samples/ThirdPerson-Combat](samples/ThirdPerson-Combat/PortReadiness.md) |
| First Person + Shooter | 42 | 26 | [samples/FirstPerson-Shooter](samples/FirstPerson-Shooter/PortReadiness.md) |
| Top Down + Strategy | 13 | 11 | [samples/TopDown-Strategy](samples/TopDown-Strategy/PortReadiness.md) |

"Can be ported with the kit alone" means no hand-work construct; most of those Blueprints still contain constructs the tools handle and check (interfaces, State Tree bindings, casts...). Each folder also has the `PortReadiness.json` an agent would read.

## What it cannot see

Only what is saved on disk. Level Blueprints, local variables, "Call Function By Name" strings and values typed into pins are not seen, and the Anim Blueprint and State Tree checks go by file markers, not by member. Treat the list as a first look, not a guarantee.

## What is in this repository

| File | What it is |
|---|---|
| `port_readiness.py` | the scan |
| `BlueprintDump/` | reads a saved Blueprint (a small .NET program: UAssetAPI, Newtonsoft.Json, ZstdSharp) |
| `BlueprintDump/source/` | its C# source and how to build the same DLL yourself (`BUILD.txt`) |
| `samples/` | the sample reports above |
| `LICENSE.txt` | the license of this free scan |
| `THIRD-PARTY-NOTICES.txt` | licenses of the libraries in `BlueprintDump/` |

## BlueprintPortKit

BlueprintPortKit is a separate, paid Unreal Engine 5.8 editor plugin that does the Blueprint side of a Blueprint-to-C++ port: it re-points every caller of a moved function, deletes what C++ replaced (and refuses while anything still uses it), reparents after a clash check, swaps Blueprint structs, enums and interfaces for their C++ versions, and rebinds State Tree properties. Every tool has a dry run that lists the plan first.

Questions and bug reports: open an issue here or write to rgruszkowski@seznam.cz.
