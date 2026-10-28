# Port readiness: ThirdPerson, Variant_Combat

Generated 2026-10-28 by `port_readiness.py` (read-only, from the saved files). Content root `<YourProject>/Content`, mounted at `/Game`, saved by UE 5.8.

## Summary

- 37 Blueprints, 0 structs, 0 enums.
- 32 need no hand work: the kit's tools can port them (26 of them contain constructs the tools handle and check in the dry run). 5 contain at least one construct that stays hand work.
- 0 cycle(s) of Blueprints that refer to each other; 0 file(s) BlueprintDump could not read.

## Can be ported with the kit alone

32 Blueprint(s), in port order: BP_CameraShake_Hit_Enemy, BP_CameraShake_Hit_Player, BP_CombatAIController, BP_ThirdPersonCharacter, BP_ThirdPersonPlayerController, BPI_Activatable, BPI_Attacker, BPI_Damageable, BPI_TouchInterface_Combat, EnvQueryContext_Player, StateTreeCondition_IsCharacterGrounded, StateTreeTask_FaceActor, StateTreeTask_FaceLocation, StateTreeTask_GetPlayerInfo, StateTreeTask_SetCharacterSpeed, AN_AttackCombo, AN_AttackDamage, AN_ChargedAttack, BP_Combat_ActivationVolume, BP_Combat_Dummy, BP_Combat_LavaFloor, BP_CombatEnemy, BP_ThirdPersonGameMode, BP_Combat_EnemySpawner, BP_CombatPlayerController, EnvQueryContext_Danger, StateTreeCondition_IsInDanger, StateTreeTask_ChargedAttack, StateTreeTask_ComboAttack, StateTreeTask_WaitForLanding, BP_Combat_CheckpointVolume, BP_CombatGameMode

## Handled by the kit, checked in the dry run

| Construct | Blueprints | Occurrences | What the kit does, and what stays by hand |
|---|---|---|---|
| Interfaces | 16 | 30 | `swap_interface` moves the Blueprints that implement a Blueprint Interface onto a C++ interface (names with spaces match); a Blueprint can also keep its Blueprint Interface while it is ported. Message calls in levels and unloaded Blueprints stay a WARNING, and the old interface is deleted by hand |
| Event dispatchers | 6 | 13 | the reparent preflight compares a dispatcher with the C++ delegate of its name, and `repoint_dispatcher_to_component` moves its users to a component; renaming or retyping a dispatcher stays hand work |
| Widget bindings | 0 | 0 | the delete tools refuse while a binding names the member and `rename_member_variable` carries a variable binding along; a bound function in a re-point is a WARNING to bind by hand |
| Replication | 0 | 0 | the reparent preflight compares replication (flag, RepNotify, condition) and the re-point tools the RPC kind; a difference is a WARNING and a real run is refused |
| Casts | 5 | 7 | they keep working while the Blueprint they cast to stays (the usual port: the Blueprint becomes a thin child of the C++ class); only a cast to a Blueprint you delete or replace with a C++ class is hand work |
| Soft references | 0 | 0 | they keep working while the asset they point at stays; only one to a Blueprint you delete or replace with a C++ class is hand work |
| State Tree | 11 | 11 | `rebind_state_tree_property` and `remove_state_tree_binding` handle plain property bindings; output, task completion and property function bindings are hand work (the scan cannot tell them apart) |

## Hand work: what the kit cannot do, found in this project

| Construct | Blueprints | Occurrences | What it means |
|---|---|---|---|
| Timelines | 2 | 2 | no tool moves a Timeline: its curves and update logic are rewritten in C++ by hand |
| Custom macros | 0 | 0 | logic inside a macro graph is not seen by the call and delete tools |
| Anim Blueprint | 1 | 1 | Property Access nodes cannot be edited: the delete tools only warn |
| Reparent by hand | 3 | 3 | `reparent_blueprint` refuses Widget, Animation and Level Blueprints: reparent them in the editor (File > Reparent Blueprint) |

## Port order (bottom-up)

A Blueprint comes after the Blueprints it needs. Everything in one wave can be ported in any order; wave 0 needs no other Blueprint of the project.

- Wave 0: ABP_Manny_Combat, BP_CameraShake_Hit_Enemy, BP_CameraShake_Hit_Player, BP_CombatAIController, BP_ThirdPersonCharacter, BP_ThirdPersonPlayerController, BPI_Activatable, BPI_Attacker, BPI_Damageable, BPI_TouchInterface_Combat, EnvQueryContext_Player, StateTreeCondition_IsCharacterGrounded, StateTreeTask_FaceActor, StateTreeTask_FaceLocation, StateTreeTask_GetPlayerInfo, StateTreeTask_SetCharacterSpeed, UI_LifeBar
- Wave 1: AN_AttackCombo, AN_AttackDamage, AN_ChargedAttack, BP_Combat_ActivationVolume, BP_Combat_DamageableBox, BP_Combat_Dummy, BP_Combat_LavaFloor, BP_CombatCharacter, BP_CombatEnemy, BP_ThirdPersonGameMode, UI_TouchInterface_Combat
- Wave 2: BP_Combat_EnemySpawner, BP_CombatPlayerController, EnvQueryContext_Danger, StateTreeCondition_IsInDanger, StateTreeTask_ChargedAttack, StateTreeTask_ComboAttack, StateTreeTask_WaitForLanding
- Wave 3: BP_Combat_CheckpointVolume, BP_CombatGameMode

## Blueprints

| # | Blueprint | Kind | Parent | Statements | Needs | Used by | Hand work | Handled and checked |
|---|---|---|---|---|---|---|---|---|
| 1 | ABP_Manny_Combat | Anim Blueprint | AnimInstance | 129 | 0 | 2 | reparent by hand 1, anim blueprint 1 | casts 1 |
| 2 | BP_CameraShake_Hit_Enemy | Blueprint | DefaultCameraShakeBase | 0 | 0 | 1 | none | none |
| 3 | BP_CameraShake_Hit_Player | Blueprint | DefaultCameraShakeBase | 0 | 0 | 1 | none | none |
| 4 | BP_CombatAIController | Blueprint | AIController | 0 | 0 | 2 | none | state tree 1 |
| 5 | BP_ThirdPersonCharacter | Blueprint | Character | 264 | 0 | 1 | none | interfaces 1 |
| 6 | BP_ThirdPersonPlayerController | Blueprint | PlayerController | 75 | 0 | 1 | none | none |
| 7 | BPI_Activatable | Blueprint Interface | Interface | 6 | 0 | 2 | none | interfaces 1 |
| 8 | BPI_Attacker | Blueprint Interface | Interface | 6 | 0 | 5 | none | interfaces 1 |
| 9 | BPI_Damageable | Blueprint Interface | Interface | 8 | 0 | 5 | none | interfaces 1 |
| 10 | BPI_TouchInterface_Combat | Blueprint Interface | Interface | 14 | 0 | 2 | none | interfaces 1 |
| 11 | EnvQueryContext_Player | Blueprint | EnvQueryContext_BlueprintBase | 17 | 0 | 2 | none | none |
| 12 | StateTreeCondition_IsCharacterGrounded | Blueprint | StateTreeConditionBlueprintBase | 11 | 0 | 1 | none | state tree 1 |
| 13 | StateTreeTask_FaceActor | Blueprint | StateTreeTaskBlueprintBase | 34 | 0 | 1 | none | state tree 1 |
| 14 | StateTreeTask_FaceLocation | Blueprint | StateTreeTaskBlueprintBase | 34 | 0 | 1 | none | state tree 1 |
| 15 | StateTreeTask_GetPlayerInfo | Blueprint | StateTreeTaskBlueprintBase | 125 | 0 | 1 | none | state tree 1 |
| 16 | StateTreeTask_SetCharacterSpeed | Blueprint | StateTreeTaskBlueprintBase | 19 | 0 | 1 | none | state tree 1 |
| 17 | UI_LifeBar | Widget Blueprint | UserWidget | 34 | 0 | 2 | reparent by hand 1 | none |
| 18 | AN_AttackCombo | Blueprint | AnimNotify | 24 | 1 | 1 | none | interfaces 1 |
| 19 | AN_AttackDamage | Blueprint | AnimNotify | 24 | 1 | 2 | none | interfaces 1 |
| 20 | AN_ChargedAttack | Blueprint | AnimNotify | 24 | 1 | 1 | none | interfaces 1 |
| 21 | BP_Combat_ActivationVolume | Blueprint | Actor | 143 | 1 | 1 | none | interfaces 2 |
| 22 | BP_Combat_DamageableBox | Blueprint | Actor | 193 | 1 | 52 | timelines 1 | interfaces 1 |
| 23 | BP_Combat_Dummy | Blueprint | Actor | 56 | 1 | 1 | none | interfaces 1 |
| 24 | BP_Combat_LavaFloor | Blueprint | Actor | 29 | 1 | 1 | none | interfaces 1 |
| 25 | BP_CombatCharacter | Blueprint | Character | 1247 | 7 | 3 | timelines 1 | interfaces 5, casts 2 |
| 26 | BP_CombatEnemy | Blueprint | Character | 690 | 5 | 7 | none | interfaces 3, event dispatchers 5, casts 1, state tree 1 |
| 27 | BP_ThirdPersonGameMode | Blueprint | GameModeBase | 0 | 2 | 1 | none | none |
| 28 | UI_TouchInterface_Combat | Widget Blueprint | UserWidget | 178 | 1 | 1 | reparent by hand 1 | interfaces 7 |
| 29 | BP_Combat_EnemySpawner | Blueprint | Actor | 230 | 2 | 4 | none | interfaces 2, event dispatchers 1 |
| 30 | BP_CombatPlayerController | Blueprint | PlayerController | 134 | 2 | 2 | none | event dispatchers 1 |
| 31 | EnvQueryContext_Danger | Blueprint | EnvQueryContext_BlueprintBase | 26 | 1 | 1 | none | casts 1 |
| 32 | StateTreeCondition_IsInDanger | Blueprint | StateTreeConditionBlueprintBase | 27 | 1 | 1 | none | state tree 1 |
| 33 | StateTreeTask_ChargedAttack | Blueprint | StateTreeTaskBlueprintBase | 56 | 1 | 1 | none | event dispatchers 2, state tree 1 |
| 34 | StateTreeTask_ComboAttack | Blueprint | StateTreeTaskBlueprintBase | 55 | 1 | 1 | none | event dispatchers 2, state tree 1 |
| 35 | StateTreeTask_WaitForLanding | Blueprint | StateTreeTaskBlueprintBase | 52 | 1 | 1 | none | event dispatchers 2, state tree 1 |
| 36 | BP_Combat_CheckpointVolume | Blueprint | Actor | 37 | 2 | 1 | none | casts 2 |
| 37 | BP_CombatGameMode | Blueprint | GameModeBase | 103 | 2 | 1 | none | none |

## Constructs in detail

- **ABP_Manny_Combat**, casts (handled): cast to Character
- **ABP_Manny_Combat**, reparent by hand (hand work): Anim Blueprint
- **ABP_Manny_Combat**, anim blueprint (hand work): is an Anim Blueprint
- **BP_CombatAIController**, state tree (handled): used by ST_CombatEnemy
- **BP_ThirdPersonCharacter**, interfaces (handled): implements BPI_TouchInterface_C
- **BPI_Activatable**, interfaces (handled): is a Blueprint Interface
- **BPI_Attacker**, interfaces (handled): is a Blueprint Interface
- **BPI_Damageable**, interfaces (handled): is a Blueprint Interface
- **BPI_TouchInterface_Combat**, interfaces (handled): is a Blueprint Interface
- **StateTreeCondition_IsCharacterGrounded**, state tree (handled): used by ST_CombatEnemy
- **StateTreeTask_FaceActor**, state tree (handled): used by ST_CombatEnemy
- **StateTreeTask_FaceLocation**, state tree (handled): used by ST_CombatEnemy
- **StateTreeTask_GetPlayerInfo**, state tree (handled): used by ST_CombatEnemy
- **StateTreeTask_SetCharacterSpeed**, state tree (handled): used by ST_CombatEnemy
- **UI_LifeBar**, reparent by hand (hand work): Widget Blueprint
- **AN_AttackCombo**, interfaces (handled): message BPI_Attacker_C.Check Combo
- **AN_AttackDamage**, interfaces (handled): message BPI_Attacker_C.Do Attack Trace
- **AN_ChargedAttack**, interfaces (handled): message BPI_Attacker_C.Check Charged Attack
- **BP_Combat_ActivationVolume**, interfaces (handled): message BPI_Activatable_C.Activate Interaction; message BPI_Activatable_C.Deactivate Interaction
- **BP_Combat_DamageableBox**, interfaces (handled): implements BPI_Damageable_C
- **BP_Combat_DamageableBox**, timelines (hand work): Fade Timeline
- **BP_Combat_Dummy**, interfaces (handled): implements BPI_Damageable_C
- **BP_Combat_LavaFloor**, interfaces (handled): message BPI_Damageable_C.Apply Damage
- **BP_CombatCharacter**, interfaces (handled): implements BPI_Attacker_C; implements BPI_Damageable_C; implements BPI_TouchInterface_Combat_C; message BPI_Damageable_C.Apply Damage; message BPI_Damageable_C.Notify Danger
- **BP_CombatCharacter**, timelines (hand work): Toggle Shoulder Timeline
- **BP_CombatCharacter**, casts (handled): cast to PlayerController; cast to UI_LifeBar_C
- **BP_CombatEnemy**, interfaces (handled): implements BPI_Attacker_C; implements BPI_Damageable_C; message BPI_Damageable_C.Apply Damage
- **BP_CombatEnemy**, event dispatchers (handled): call On Attack Completed x2; call On Enemy Died; declares On Attack Completed; declares On Enemy Died
- **BP_CombatEnemy**, casts (handled): cast to UI_LifeBar_C
- **BP_CombatEnemy**, state tree (handled): used by ST_CombatEnemy
- **UI_TouchInterface_Combat**, interfaces (handled): message BPI_TouchInterface_Combat_C.Primary Thumbstick; message BPI_TouchInterface_Combat_C.Secondary Thumbstick; message BPI_TouchInterface_Combat_C.Touch Charged Attack End; message BPI_TouchInterface_Combat_C.Touch Charged Attack Start; message BPI_TouchInterface_Combat_C.Touch Combo Attack End; message BPI_TouchInterface_Combat_C.Touch Combo Attack Start; message BPI_TouchInterface_Combat_C.Touch Toggle Camera
- **UI_TouchInterface_Combat**, reparent by hand (hand work): Widget Blueprint
- **BP_Combat_EnemySpawner**, interfaces (handled): implements BPI_Activatable_C; message BPI_Activatable_C.Activate Interaction
- **BP_Combat_EnemySpawner**, event dispatchers (handled): bind On Enemy Died
- **BP_CombatPlayerController**, event dispatchers (handled): bind OnDestroyed
- **EnvQueryContext_Danger**, casts (handled): cast to BP_CombatEnemy_C
- **StateTreeCondition_IsInDanger**, state tree (handled): used by ST_CombatEnemy
- **StateTreeTask_ChargedAttack**, event dispatchers (handled): bind On Attack Completed; unbind On Attack Completed
- **StateTreeTask_ChargedAttack**, state tree (handled): used by ST_CombatEnemy
- **StateTreeTask_ComboAttack**, event dispatchers (handled): bind On Attack Completed; unbind On Attack Completed
- **StateTreeTask_ComboAttack**, state tree (handled): used by ST_CombatEnemy
- **StateTreeTask_WaitForLanding**, event dispatchers (handled): bind LandedDelegate; unbind LandedDelegate
- **StateTreeTask_WaitForLanding**, state tree (handled): used by ST_CombatEnemy
- **BP_Combat_CheckpointVolume**, casts (handled): cast to BP_CombatCharacter_C; cast to BP_CombatPlayerController_C

---

This report was made by the free BlueprintPortKit Readiness Scan. BlueprintPortKit is the plugin that does the Blueprint side of a Blueprint-to-C++ port for the Blueprints listed above: it re-points every caller of a moved function, deletes what C++ replaced (and refuses while anything still uses it), reparents after a clash check, swaps Blueprint structs, enums and interfaces for their C++ versions, and rebinds State Tree properties. Every tool has a dry run that lists the plan first. More: rgruszkowski@seznam.cz
