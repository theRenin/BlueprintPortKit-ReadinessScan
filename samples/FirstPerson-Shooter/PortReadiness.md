# Port readiness: FirstPerson, Variant_Shooter

Generated 2026-10-28 by `port_readiness.py` (read-only, from the saved files). Content root `<YourProject>/Content`, mounted at `/Game`, saved by UE 5.8.

## Summary

- 42 Blueprints, 1 structs, 0 enums.
- 26 of the Blueprints need no hand work: the kit's tools can port them (19 of them contain constructs the tools handle and check in the dry run). 16 contain at least one construct that stays hand work.
- 3 cycle(s) of Blueprints that refer to each other; 0 file(s) BlueprintDump could not read.

## Can be ported with the kit alone

26 Blueprint(s), in port order: BP_FirstPersonCameraManager, BP_ShooterProjectileBase, BPI_Shooter, BPI_Teammate, BPI_Touch_Shooter, StateTreeTask_FaceActor, StateTreeTask_FaceLocation, StateTreeTask_SetRandomFloat, BP_FirstPersonPlayerController, BP_ShooterProjectile_Grenade, BP_FirstPersonGameMode, BP_ShooterWeaponBase, BPI_Pickups, BPI_WeaponHolder, BP_ShooterPlayerController, BP_ShooterWeapon_GrenadeLauncher, BP_ShooterWeapon_Rifle, BP_ShooterGameMode, BP_ShooterWeapon_Pistol, BP_ShooterAIController, BP_ShooterNPC, BP_ShooterNPCSpawner, EnvQueryContext_Target, StateTreeCondition_HasLineOfSightToTarget, StateTreeTask_SenseEnemies, StateTreeTask_ShootAtTarget

## Handled by the kit, checked in the dry run

| Construct | Blueprints | Occurrences | What the kit does, and what stays by hand |
|---|---|---|---|
| Interfaces | 16 | 43 | `swap_interface` moves the Blueprints that implement a Blueprint Interface onto a C++ interface (names with spaces match); a Blueprint can also keep its Blueprint Interface while it is ported. Message calls in levels and unloaded Blueprints stay a WARNING, and the old interface is deleted by hand |
| Event dispatchers | 8 | 13 | the reparent preflight compares a dispatcher with the C++ delegate of its name, and `repoint_dispatcher_to_component` moves its users to a component; renaming or retyping a dispatcher stays hand work |
| Widget bindings | 0 | 0 | the delete tools refuse while a binding names the member and `rename_member_variable` carries a variable binding along; a bound function in a re-point is a WARNING to bind by hand |
| Replication | 0 | 0 | the reparent preflight compares replication (flag, RepNotify, condition) and the re-point tools the RPC kind; a difference is a WARNING and a real run is refused |
| Casts | 11 | 11 | they keep working while the Blueprint they cast to stays (the usual port: the Blueprint becomes a thin child of the C++ class); only a cast to a Blueprint you delete or replace with a C++ class is hand work |
| Soft references | 0 | 0 | they keep working while the asset they point at stays; only one to a Blueprint you delete or replace with a C++ class is hand work |
| State Tree | 9 | 11 | `rebind_state_tree_property` and `remove_state_tree_binding` handle plain property bindings; output, task completion and property function bindings are hand work (the scan cannot tell them apart) |

## Hand work: what the kit cannot do, found in this project

| Construct | Blueprints | Occurrences | What it means |
|---|---|---|---|
| Timelines | 3 | 3 | no tool moves a Timeline: its curves and update logic are rewritten in C++ by hand |
| Custom macros | 0 | 0 | logic inside a macro graph is not seen by the call and delete tools |
| Anim Blueprint | 10 | 12 | Property Access nodes cannot be edited: the delete tools only warn |
| Reparent by hand | 8 | 8 | `reparent_blueprint` refuses Widget, Animation and Level Blueprints: reparent them in the editor (File > Reparent Blueprint) |

## Port order (bottom-up)

A Blueprint comes after the Blueprints it needs. Everything in one wave can be ported in any order; wave 0 needs no other Blueprint of the project.

- Wave 0: ABP_TP_Pistol, ABP_TP_Rifle, BP_FirstPersonCameraManager, BP_Shooter_GrenadeExplosion, BP_ShooterProjectileBase, BPI_Shooter, BPI_Teammate, BPI_Touch_Shooter, Ctrl_HandAdjusment, Ctrl_HandAdjusment_Pistol, CtrlRig_FPWarp, StateTreeTask_FaceActor, StateTreeTask_FaceLocation, StateTreeTask_SetRandomFloat, UI_ShooterBulletCounter
- Wave 1: ABP_FP_Copy, BP_FirstPersonPlayerController, BP_ShooterProjectile_Bullet, BP_ShooterProjectile_Grenade, UI_TouchInterface_Shooter
- Wave 2: BP_FirstPersonCharacter
- Wave 3: ABP_FP_Weapon, BP_FirstPersonGameMode, BP_ShooterCharacter, BP_ShooterWeaponBase, BPI_Pickups, BPI_WeaponHolder
- Wave 4: ABP_FP_Pistol, BP_ShooterPlayerController, BP_ShooterWeapon_GrenadeLauncher, BP_ShooterWeapon_Rifle, ST_WeaponTableRow
- Wave 5: BP_ShooterGameMode, BP_ShooterPickup, BP_ShooterWeapon_Pistol, UI_Shooter
- Wave 6: BP_ShooterAIController, BP_ShooterNPC
- Wave 7: BP_ShooterNPCSpawner, EnvQueryContext_Target, StateTreeCondition_HasLineOfSightToTarget, StateTreeTask_SenseEnemies, StateTreeTask_ShootAtTarget
- Cycle C1: ABP_FP_Weapon, BP_ShooterCharacter, BP_ShooterWeaponBase, BPI_Pickups, BPI_WeaponHolder refer to each other; port them in one item or break the cycle first.
- Cycle C2: BP_ShooterAIController, BP_ShooterNPC refer to each other; port them in one item or break the cycle first.
- Cycle C3: BP_ShooterGameMode, UI_Shooter refer to each other; port them in one item or break the cycle first.

## Blueprints

| # | Blueprint | Kind | Parent | Statements | Needs | Used by | Hand work | Handled and checked |
|---|---|---|---|---|---|---|---|---|
| 1 | ABP_TP_Pistol | Anim Blueprint | AnimInstance | 163 | 0 | 1 | reparent by hand 1, anim blueprint 1 | casts 1 |
| 2 | ABP_TP_Rifle | Anim Blueprint | AnimInstance | 162 | 0 | 2 | reparent by hand 1, anim blueprint 1 | casts 1 |
| 3 | BP_FirstPersonCameraManager | Blueprint | PlayerCameraManager | 0 | 0 | 1 | none | none |
| 4 | BP_Shooter_GrenadeExplosion | Blueprint | Pawn | 48 | 0 | 1 | timelines 1 | none |
| 5 | BP_ShooterProjectileBase | Blueprint | Actor | 282 | 0 | 4 | none | casts 1 |
| 6 | BPI_Shooter | Blueprint Interface | Interface | 10 | 0 | 6 | none | interfaces 1 |
| 7 | BPI_Teammate | Blueprint Interface | Interface | 4 | 0 | 3 | none | interfaces 1 |
| 8 | BPI_Touch_Shooter | Blueprint Interface | Interface | 6 | 0 | 2 | none | interfaces 1 |
| 9 | Ctrl_HandAdjusment | Blueprint | ControlRig | 0 | 0 | 1 | anim blueprint 1 | none |
| 10 | Ctrl_HandAdjusment_Pistol | Blueprint | ControlRig | 0 | 0 | 1 | anim blueprint 1 | none |
| 11 | CtrlRig_FPWarp | Blueprint | ControlRig | 0 | 0 | 1 | anim blueprint 1 | none |
| 12 | StateTreeTask_FaceActor | Blueprint | StateTreeTaskBlueprintBase | 36 | 0 | 1 | none | state tree 1 |
| 13 | StateTreeTask_FaceLocation | Blueprint | StateTreeTaskBlueprintBase | 39 | 0 | 1 | none | state tree 1 |
| 14 | StateTreeTask_SetRandomFloat | Blueprint | StateTreeTaskBlueprintBase | 42 | 0 | 1 | none | state tree 1 |
| 15 | UI_ShooterBulletCounter | Widget Blueprint | UserWidget | 92 | 0 | 1 | reparent by hand 1 | none |
| 16 | ABP_FP_Copy | Anim Blueprint | AnimInstance | 7 | 1 | 1 | reparent by hand 1, anim blueprint 1 | none |
| 17 | BP_FirstPersonPlayerController | Blueprint | PlayerController | 75 | 1 | 2 | none | none |
| 18 | BP_ShooterProjectile_Bullet | Blueprint | BP_ShooterProjectileBase_C | 87 | 1 | 1 | timelines 1 | none |
| 19 | BP_ShooterProjectile_Grenade | Blueprint | BP_ShooterProjectileBase_C | 25 | 2 | 1 | none | none |
| 20 | UI_TouchInterface_Shooter | Widget Blueprint | UserWidget | 175 | 1 | 2 | reparent by hand 1 | interfaces 7 |
| 21 | BP_FirstPersonCharacter | Blueprint | Character | 258 | 1 | 8 | anim blueprint 2 | interfaces 1, state tree 1 |
| 22 | ABP_FP_Weapon | Anim Blueprint | AnimInstance | 164 | 3 | 1 | reparent by hand 1, anim blueprint 1 | casts 1 |
| 23 | BP_FirstPersonGameMode | Blueprint | GameModeBase | 0 | 2 | 1 | none | none |
| 24 | BP_ShooterCharacter | Blueprint | BP_FirstPersonCharacter_C | 763 | 8 | 5 | anim blueprint 2 | interfaces 10, casts 1 |
| 25 | BP_ShooterWeaponBase | Blueprint | Actor | 367 | 5 | 9 | none | interfaces 8, event dispatchers 1, casts 1 |
| 26 | BPI_Pickups | Blueprint Interface | Interface | 2 | 1 | 1 | none | interfaces 1 |
| 27 | BPI_WeaponHolder | Blueprint Interface | Interface | 18 | 1 | 4 | none | interfaces 1 |
| 28 | ABP_FP_Pistol | Anim Blueprint | AnimInstance | 164 | 3 | 1 | reparent by hand 1, anim blueprint 1 | casts 1 |
| 29 | BP_ShooterPlayerController | Blueprint | BP_FirstPersonPlayerController_C | 274 | 6 | 1 | none | interfaces 4, event dispatchers 1 |
| 30 | BP_ShooterWeapon_GrenadeLauncher | Blueprint | BP_ShooterWeaponBase_C | 0 | 3 | 1 | none | none |
| 31 | BP_ShooterWeapon_Rifle | Blueprint | BP_ShooterWeaponBase_C | 0 | 1 | 1 | none | none |
| 32 | ST_WeaponTableRow | Struct |  | 0 | 1 | 2 | none | none |
| 33 | BP_ShooterGameMode | Blueprint | GameModeBase | 193 | 5 | 2 | none | interfaces 2, event dispatchers 2 |
| 34 | BP_ShooterPickup | Blueprint | Actor | 207 | 5 | 5 | timelines 1 | interfaces 1, casts 1 |
| 35 | BP_ShooterWeapon_Pistol | Blueprint | BP_ShooterWeaponBase_C | 0 | 3 | 2 | none | none |
| 36 | UI_Shooter | Widget Blueprint | UserWidget | 59 | 2 | 1 | reparent by hand 1 | interfaces 1, event dispatchers 1, casts 1 |
| 37 | BP_ShooterAIController | Blueprint | AIController | 96 | 1 | 5 | none | interfaces 1, event dispatchers 1, casts 1, state tree 2 |
| 38 | BP_ShooterNPC | Blueprint | BP_FirstPersonCharacter_C | 392 | 7 | 7 | none | interfaces 2, event dispatchers 2, state tree 2 |
| 39 | BP_ShooterNPCSpawner | Blueprint | Actor | 110 | 2 | 2 | none | interfaces 1, event dispatchers 1 |
| 40 | EnvQueryContext_Target | Blueprint | EnvQueryContext_BlueprintBase | 32 | 1 | 1 | none | casts 1 |
| 41 | StateTreeCondition_HasLineOfSightToTarget | Blueprint | StateTreeConditionBlueprintBase | 123 | 2 | 1 | none | state tree 1 |
| 42 | StateTreeTask_SenseEnemies | Blueprint | StateTreeTaskBlueprintBase | 149 | 2 | 1 | none | event dispatchers 4, state tree 1 |
| 43 | StateTreeTask_ShootAtTarget | Blueprint | StateTreeTaskBlueprintBase | 43 | 1 | 1 | none | state tree 1 |

## Constructs in detail

- **ABP_TP_Pistol**, casts (handled): cast to Character
- **ABP_TP_Pistol**, reparent by hand (hand work): Anim Blueprint
- **ABP_TP_Pistol**, anim blueprint (hand work): is an Anim Blueprint
- **ABP_TP_Rifle**, casts (handled): cast to Character
- **ABP_TP_Rifle**, reparent by hand (hand work): Anim Blueprint
- **ABP_TP_Rifle**, anim blueprint (hand work): is an Anim Blueprint
- **BP_Shooter_GrenadeExplosion**, timelines (hand work): Timeline
- **BP_ShooterProjectileBase**, casts (handled): cast to Character
- **BPI_Shooter**, interfaces (handled): is a Blueprint Interface
- **BPI_Teammate**, interfaces (handled): is a Blueprint Interface
- **BPI_Touch_Shooter**, interfaces (handled): is a Blueprint Interface
- **Ctrl_HandAdjusment**, anim blueprint (hand work): used by ABP_FP_Weapon
- **Ctrl_HandAdjusment_Pistol**, anim blueprint (hand work): used by ABP_FP_Pistol
- **CtrlRig_FPWarp**, anim blueprint (hand work): used by ABP_FP_Copy
- **StateTreeTask_FaceActor**, state tree (handled): used by ST_Shooter
- **StateTreeTask_FaceLocation**, state tree (handled): used by ST_Shooter
- **StateTreeTask_SetRandomFloat**, state tree (handled): used by ST_Shooter_ShootAtTarget
- **UI_ShooterBulletCounter**, reparent by hand (hand work): Widget Blueprint
- **ABP_FP_Copy**, reparent by hand (hand work): Anim Blueprint
- **ABP_FP_Copy**, anim blueprint (hand work): is an Anim Blueprint
- **BP_ShooterProjectile_Bullet**, timelines (hand work): Wiggle
- **UI_TouchInterface_Shooter**, interfaces (handled): message BPI_TouchInterface_C.Primary Thumbstick; message BPI_TouchInterface_C.Secondary Thumbstick; message BPI_TouchInterface_C.Touch Jump End; message BPI_TouchInterface_C.Touch Jump Start; message BPI_Touch_Shooter_C.Touch Shoot End; message BPI_Touch_Shooter_C.Touch Shoot Start; message BPI_Touch_Shooter_C.Touch Switch Weapon
- **UI_TouchInterface_Shooter**, reparent by hand (hand work): Widget Blueprint
- **BP_FirstPersonCharacter**, interfaces (handled): implements BPI_TouchInterface_C
- **BP_FirstPersonCharacter**, anim blueprint (hand work): used by ABP_FP_Pistol; used by ABP_FP_Weapon
- **BP_FirstPersonCharacter**, state tree (handled): used by ST_Shooter_ShootAtTarget
- **ABP_FP_Weapon**, casts (handled): cast to BP_ShooterCharacter_C
- **ABP_FP_Weapon**, reparent by hand (hand work): Anim Blueprint
- **ABP_FP_Weapon**, anim blueprint (hand work): is an Anim Blueprint
- **BP_ShooterCharacter**, interfaces (handled): implements BPI_Pickups_C; implements BPI_Teammate_C; implements BPI_Touch_Shooter_C; implements BPI_WeaponHolder_C; message BPI_Shooter_C.IncrementTeamScore; message BPI_Shooter_C.Update Bullet UI x3; message BPI_Shooter_C.Update Health UI x2
- **BP_ShooterCharacter**, casts (handled): cast to PlayerController
- **BP_ShooterCharacter**, anim blueprint (hand work): used by ABP_FP_Pistol; used by ABP_FP_Weapon
- **BP_ShooterWeaponBase**, interfaces (handled): message BPI_WeaponHolder_C.Add Weapon Recoil; message BPI_WeaponHolder_C.Attach Weapon Meshes; message BPI_WeaponHolder_C.Get Weapon Target Location; message BPI_WeaponHolder_C.On Semi Weapon Refire; message BPI_WeaponHolder_C.On Weapon Activated; message BPI_WeaponHolder_C.On Weapon Deactivated; message BPI_WeaponHolder_C.Play Firing Montage; message BPI_WeaponHolder_C.Update Weapon HUD
- **BP_ShooterWeaponBase**, event dispatchers (handled): bind OnDestroyed
- **BP_ShooterWeaponBase**, casts (handled): cast to Pawn
- **BPI_Pickups**, interfaces (handled): is a Blueprint Interface
- **BPI_WeaponHolder**, interfaces (handled): is a Blueprint Interface
- **ABP_FP_Pistol**, casts (handled): cast to BP_ShooterCharacter_C
- **ABP_FP_Pistol**, reparent by hand (hand work): Anim Blueprint
- **ABP_FP_Pistol**, anim blueprint (hand work): is an Anim Blueprint
- **BP_ShooterPlayerController**, interfaces (handled): implements BPI_Shooter_C; implements BPI_Teammate_C; message BPI_Teammate_C.Set Team x2
- **BP_ShooterPlayerController**, event dispatchers (handled): assign OnDestroyed
- **BP_ShooterGameMode**, interfaces (handled): implements BPI_Shooter_C; message BPI_Teammate_C.Set Team
- **BP_ShooterGameMode**, event dispatchers (handled): call Score Updated; declares Score Updated
- **BP_ShooterPickup**, interfaces (handled): message BPI_WeaponHolder_C.Add Weapon Class
- **BP_ShooterPickup**, timelines (hand work): SpawnIn
- **BP_ShooterPickup**, casts (handled): cast to StaticMesh
- **UI_Shooter**, interfaces (handled): message BPI_Shooter_C.GetTeamScore
- **UI_Shooter**, event dispatchers (handled): bind Score Updated
- **UI_Shooter**, casts (handled): cast to BP_ShooterGameMode_C
- **UI_Shooter**, reparent by hand (hand work): Widget Blueprint
- **BP_ShooterAIController**, interfaces (handled): message NavMovementInterface.StopActiveMovement
- **BP_ShooterAIController**, event dispatchers (handled): bind On Death
- **BP_ShooterAIController**, casts (handled): cast to BP_ShooterNPC_C
- **BP_ShooterAIController**, state tree (handled): used by ST_Shooter; used by ST_Shooter_ShootAtTarget
- **BP_ShooterNPC**, interfaces (handled): implements BPI_WeaponHolder_C; message BPI_Shooter_C.IncrementTeamScore
- **BP_ShooterNPC**, event dispatchers (handled): call On Death; declares On Death
- **BP_ShooterNPC**, state tree (handled): used by ST_Shooter; used by ST_Shooter_ShootAtTarget
- **BP_ShooterNPCSpawner**, interfaces (handled): message BPI_Shooter_C.Should Spawn Enemy NPCs
- **BP_ShooterNPCSpawner**, event dispatchers (handled): bind On Death
- **EnvQueryContext_Target**, casts (handled): cast to BP_ShooterAIController_C
- **StateTreeCondition_HasLineOfSightToTarget**, state tree (handled): used by ST_Shooter_ShootAtTarget
- **StateTreeTask_SenseEnemies**, event dispatchers (handled): bind OnTargetPerceptionForgotten; bind OnTargetPerceptionUpdated; unbind OnTargetPerceptionForgotten; unbind OnTargetPerceptionUpdated
- **StateTreeTask_SenseEnemies**, state tree (handled): used by ST_Shooter
- **StateTreeTask_ShootAtTarget**, state tree (handled): used by ST_Shooter_ShootAtTarget

---

This report was made by the free BlueprintPortKit Readiness Scan. BlueprintPortKit is the plugin that does the Blueprint side of a Blueprint-to-C++ port for the Blueprints listed above: it re-points every caller of a moved function, deletes what C++ replaced (and refuses while anything still uses it), reparents after a clash check, swaps Blueprint structs, enums and interfaces for their C++ versions, and rebinds State Tree properties. Every tool has a dry run that lists the plan first. More: rgruszkowski@seznam.cz
