# Port readiness: TopDown, Variant_Strategy

Generated 2026-10-28 by `port_readiness.py` (read-only, from the saved files). Content root `<YourProject>/Content`, mounted at `/Game`, saved by UE 5.8.

## Summary

- 13 Blueprints, 0 structs, 1 enums.
- 12 need no hand work: the kit's tools can port them (7 of them contain constructs the tools handle and check in the dry run). 2 contain at least one construct that stays hand work.
- 1 cycle(s) of Blueprints that refer to each other; 0 file(s) BlueprintDump could not read.

## Can be ported with the kit alone

11 Blueprint(s), in port order: BP_AssetGuideline_Strategy, BP_TopDownCharacter, BP_TopDownController, BPI_Strategy, BP_StrategyPawn, BP_StrategyUnit, BP_TopDownGameMode, EnvQueryContext_MoveGoal, BP_StrategyHUD, BP_StrategyPlayerController, BP_StrategyGameMode

## Handled by the kit, checked in the dry run

| Construct | Blueprints | Occurrences | What the kit does, and what stays by hand |
|---|---|---|---|
| Interfaces | 7 | 22 | `swap_interface` moves the Blueprints that implement a Blueprint Interface onto a C++ interface (names with spaces match); a Blueprint can also keep its Blueprint Interface while it is ported. Message calls in levels and unloaded Blueprints stay a WARNING, and the old interface is deleted by hand |
| Event dispatchers | 2 | 2 | the reparent preflight compares a dispatcher with the C++ delegate of its name, and `repoint_dispatcher_to_component` moves its users to a component; renaming or retyping a dispatcher stays hand work |
| Widget bindings | 0 | 0 | the delete tools refuse while a binding names the member and `rename_member_variable` carries a variable binding along; a bound function in a re-point is a WARNING to bind by hand |
| Replication | 0 | 0 | the reparent preflight compares replication (flag, RepNotify, condition) and the re-point tools the RPC kind; a difference is a WARNING and a real run is refused |
| Casts | 2 | 2 | they keep working while the Blueprint they cast to stays (the usual port: the Blueprint becomes a thin child of the C++ class); only a cast to a Blueprint you delete or replace with a C++ class is hand work |
| Soft references | 0 | 0 | they keep working while the asset they point at stays; only one to a Blueprint you delete or replace with a C++ class is hand work |
| State Tree | 0 | 0 | `rebind_state_tree_property` and `remove_state_tree_binding` handle plain property bindings; output, task completion and property function bindings are hand work (the scan cannot tell them apart) |

## Hand work: what the kit cannot do, found in this project

| Construct | Blueprints | Occurrences | What it means |
|---|---|---|---|
| Timelines | 0 | 0 | no tool moves a Timeline: its curves and update logic are rewritten in C++ by hand |
| Custom macros | 0 | 0 | logic inside a macro graph is not seen by the call and delete tools |
| Anim Blueprint | 0 | 0 | Property Access nodes cannot be edited: the delete tools only warn |
| Reparent by hand | 2 | 2 | `reparent_blueprint` refuses Widget, Animation and Level Blueprints: reparent them in the editor (File > Reparent Blueprint) |

## Port order (bottom-up)

A Blueprint comes after the Blueprints it needs. Everything in one wave can be ported in any order; wave 0 needs no other Blueprint of the project.

- Wave 0: BP_AssetGuideline_Strategy, BP_TopDownCharacter, BP_TopDownController, BPI_Strategy, Enum_InputModes
- Wave 1: BP_StrategyPawn, BP_StrategyUnit, BP_TopDownGameMode, EnvQueryContext_MoveGoal, UI_Strategy
- Wave 2: BP_StrategyHUD, BP_StrategyPlayerController, WBP_StrategyMobileControls
- Wave 3: BP_StrategyGameMode
- Cycle C1: BP_StrategyPlayerController, WBP_StrategyMobileControls refer to each other; port them in one item or break the cycle first.

## Blueprints

| # | Blueprint | Kind | Parent | Statements | Needs | Used by | Hand work | Handled and checked |
|---|---|---|---|---|---|---|---|---|
| 1 | BP_AssetGuideline_Strategy | Blueprint | AssetGuideline | 0 | 0 | 0 | none | none |
| 2 | BP_TopDownCharacter | Blueprint | Character | 0 | 0 | 1 | none | none |
| 3 | BP_TopDownController | Blueprint | PlayerController | 440 | 0 | 1 | none | event dispatchers 1 |
| 4 | BPI_Strategy | Blueprint Interface | Interface | 22 | 0 | 6 | none | interfaces 1 |
| 5 | Enum_InputModes | Enum |  | 0 | 0 | 0 | none | none |
| 6 | BP_StrategyPawn | Blueprint | Pawn | 127 | 1 | 2 | none | interfaces 1 |
| 7 | BP_StrategyUnit | Blueprint | Character | 350 | 1 | 8 | none | interfaces 2, event dispatchers 1, casts 1 |
| 8 | BP_TopDownGameMode | Blueprint | GameModeBase | 0 | 2 | 1 | none | none |
| 9 | EnvQueryContext_MoveGoal | Blueprint | EnvQueryContext_BlueprintBase | 21 | 1 | 2 | none | interfaces 1 |
| 10 | UI_Strategy | Widget Blueprint | UserWidget | 153 | 1 | 1 | reparent by hand 1 | interfaces 1 |
| 11 | BP_StrategyHUD | Blueprint | HUD | 291 | 3 | 1 | none | interfaces 3 |
| 12 | BP_StrategyPlayerController | Blueprint | PlayerController | 1548 | 4 | 2 | none | interfaces 13, casts 1 |
| 13 | WBP_StrategyMobileControls | Widget Blueprint | UserWidget | 65 | 1 | 1 | reparent by hand 1 | none |
| 14 | BP_StrategyGameMode | Blueprint | GameModeBase | 14 | 3 | 1 | none | none |

## Constructs in detail

- **BP_TopDownController**, event dispatchers (handled): assign OnDestroyed
- **BPI_Strategy**, interfaces (handled): is a Blueprint Interface
- **BP_StrategyPawn**, interfaces (handled): implements BPI_Strategy_C
- **BP_StrategyUnit**, interfaces (handled): implements BPI_Strategy_C; message BPI_Strategy_C.Interact
- **BP_StrategyUnit**, event dispatchers (handled): bind OnQueryFinishedEvent
- **BP_StrategyUnit**, casts (handled): cast to BP_StrategyUnit_C
- **EnvQueryContext_MoveGoal**, interfaces (handled): message BPI_Strategy_C.Get Movement Goal
- **UI_Strategy**, interfaces (handled): implements BPI_Strategy_C
- **UI_Strategy**, reparent by hand (hand work): Widget Blueprint
- **BP_StrategyHUD**, interfaces (handled): implements BPI_Strategy_C; message BPI_Strategy_C.Drag Select Result; message BPI_Strategy_C.Pass Selected Units
- **BP_StrategyPlayerController**, interfaces (handled): implements BPI_Strategy_C; message BPI_Strategy_C.Drag Select Update x4; message BPI_Strategy_C.Move Unit To; message BPI_Strategy_C.Unit Deselected x2; message BPI_Strategy_C.Unit Selected x3; message BPI_Strategy_C.Zoom Modifier x2
- **BP_StrategyPlayerController**, casts (handled): cast to BP_StrategyPawn_C
- **WBP_StrategyMobileControls**, reparent by hand (hand work): Widget Blueprint

---

This report was made by the free BlueprintPortKit Readiness Scan. BlueprintPortKit is the plugin that does the Blueprint side of a Blueprint-to-C++ port for the Blueprints listed above: it re-points every caller of a moved function, deletes what C++ replaced (and refuses while anything still uses it), reparents after a clash check, swaps Blueprint structs, enums and interfaces for their C++ versions, and rebinds State Tree properties. Every tool has a dry run that lists the plan first. More: rgruszkowski@seznam.cz
