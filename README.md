# TS4 Unofficial Fixes

Script mods that fix bugs in the gameplay code of **The Sims 4**. Each fix is a separate `.ts4script`: pick the ones you want.

Tested on game version **1.128.90** (September 2026).

## Fixes

| Fix | What goes wrong in the base game | Pack | Download |
|---|---|---|---|
| **Service NPCs billed but never coming** | If you load a lot while the maid, gardener, etc. is scheduled, the visit is "performed" off-screen and billed, even though the slot is still running. The NPC never shows up. | Base game | [UnofficialFix_service_npc_offscreen](dist/UnofficialFix_service_npc_offscreen.ts4script) |
| **Organizations recruiting new members every event** | Organization events never reuse the existing members: each event recruits new NPCs, and they are added to the member list every time. | Discover University, Eco Lifestyle, StrangerVille… | [UnofficialFix_organization_members](dist/UnofficialFix_organization_members.ts4script) |
| **Schedules dying after a loading screen** | When a schedule entry with a random start fires after its time window (typically during a loading screen), the game throws `empty range for randrange()` and that schedule stops for the rest of the session. Windows crossing Saturday→Sunday can also be delayed by a whole week. | Base game | [UnofficialFix_scheduler_random_window](dist/UnofficialFix_scheduler_random_window.ts4script) |
| **Timed relationship bits lasting too long** | Timed relationship bits restart part of their timer on every load or lot travel. A 100 minute bit saved at 60 and reloaded still has 70 minutes left 30 minutes later. | Base game | [UnofficialFix_relbit_timeout](dist/UnofficialFix_relbit_timeout.ts4script) |
| **Childhood inspirations stuck after loading** | Suggested inspirations waiting in the queue are never shown again after loading a save. | Growing Together | [UnofficialFix_childhood_inspiration_refresh](dist/UnofficialFix_childhood_inspiration_refresh.ts4script) |
| **Narrative rewards lost** | When two world narratives with rewards for every sim are queued, the second one is dropped. | Base game, packs using narratives | [UnofficialFix_narrative_loot_queue](dist/UnofficialFix_narrative_loot_queue.ts4script) |
| **Street utility shut-off error** | Changing the venue of a residential lot during a street utility shut-off throws an `IndexError` and the lot's utilities are not turned back on. | Eco Lifestyle | [UnofficialFix_street_utility_venue_change](dist/UnofficialFix_street_utility_venue_change.ts4script) |
| **"Voting closes soon" warning never shown** | The warning before the end of civic policy voting is never scheduled after the first week of a save. | Eco Lifestyle | [UnofficialFix_civic_vote_warning](dist/UnofficialFix_civic_vote_warning.ts4script) |
| **Situation data never cleaned up** | The situation manager is supposed to drop data of sims that left, but never does. The table grows during the whole session. | Base game | [UnofficialFix_situation_sim_data_prune](dist/UnofficialFix_situation_sim_data_prune.ts4script) |

Related player reports: [Maid never coming but charging money?](https://forums.thesims.com/en_US/discussion/790918/maid-never-coming-but-charging-money), [Maid not showing up](https://forums.ea.com/idea/the-sims-4-bug-reports-en/maid-not-showing-up/13192123), [[DU] Student organizations assign random non-student Sims as members](https://forums.ea.com/idea/the-sims-4-bug-reports-en/du-student-organizations-assign-random-non-student-sims-as-members/13315354).

## Install

1. Download the `.ts4script` files you want from [`dist/`](dist) or from the [Releases](../../releases) page.
2. Put them in `Documents\Electronic Arts\The Sims 4\Mods\` (directly in `Mods` or one subfolder deep, not deeper).
3. In game: *Options → Game Options → Other* → enable **Custom Content and Mods** and **Script Mods Allowed**, then restart.

To check that they are running, open the cheat console (`Ctrl+Shift+C`) and type `ufix.status`. Each fix reports whether it is active and how many times it kicked in.

To uninstall, delete the files.

## How the fixes behave

- **They only replace the exact code they fix.** Before patching, each fix checks a fingerprint of the original game function. If EA changed that function in a patch, or another mod already replaced it, the fix does nothing and writes why in `Mods/ts4_unofficial_fixes.log`. A game update can disable a fix, but it can never make it apply on top of different code.
- **The fixes are minimal.** The replacement functions are EA's code with the faulty lines corrected. The technical notes below and the comment at the top of each file explain what changed.
- **No tuning or save data is modified**, and nothing is written to your save that would remain after removing the mod.
- **Compatibility:** none of the patched functions are touched by MC Command Center, WickedWhims, Lot 51 Core Library or the simulation lag mods (Simulation Flow Unleashed, Simulation Lag Fix, Queue Guard…).

## Technical notes

| Fix | Function | Cause | Change |
|---|---|---|---|
| service_npc_offscreen | `ServiceNpcService._fake_perform_services_if_necessary` | `now + min_duration <= alarm_data.end_time` compares an absolute date with a time of the week, so the check is always false after the first week. | End time converted to an absolute date in the week of the service. |
| organization_members | `OrganizationService.generate_organization_members` | `valid_org_member_ids = []` is followed by `for org_member_id in valid_org_member_ids`: the second filter pass loops over an empty list. | The second pass runs over the cleaned member list. |
| scheduler_random_window | `WeeklySchedule._alarm_callback` | `random.randint(0, (end_time - now_in_week).in_ticks())` gets a negative bound when the alarm is late, and the exception skips `schedule_next_alarm()`. | Remaining time clamped to the window (0 when late, minus one week when the window wraps). |
| relbit_timeout | `BitTimeoutData.load_bit_timeout` | `_set_alarm()` resets `_start_time` to now after loading, so the elapsed time saved next is only the time since the last load. | Start time moved back by the elapsed time that was loaded. |
| childhood_inspiration_refresh | `SuggestedAspirationsManager.load` | The refresh alarm is only created when adding to an empty queue, and `load()` refills the queue without creating it. | Alarm created after loading when the queue is not empty. |
| narrative_loot_queue | `NarrativeService.update` | Processes `_pending_narrative_loots[0]`, then removes it with `.pop()`, which removes the last entry. | `.pop(0)`. |
| street_utility_venue_change | `StreetUtilityShutoffEffect._on_venue_type_changed` | `del self._zone_ids_impacted[zone_id]` on a list. | `.remove(zone_id)`. |
| civic_vote_warning | `BaseCivicPolicyProviderServiceMixin._set_next_warn_alarm` | `self._voting_close_time - now`, where `_voting_close_time` is a time of the week. | `now.time_to_week_time(self._voting_close_time)`, as used elsewhere in the class. |
| situation_sim_data_prune | `SituationManager._prune_sim_data` | `sim_data.is_blacklisted == False` compares the method object instead of calling it. | `not sim_data.is_blacklisted()`. |

Every cause was checked against the game's compiled bytecode, not just decompiled source, since decompilers sometimes produce misleading code.

## Building from source

The game runs Python 3.7, so the scripts must be compiled with Python 3.7:

```
py -3.7 build.py
```

This writes one `.ts4script` per file of `src/` into `dist/`. `src/_common.py` holds the shared code (fingerprint check, log, `ufix.status`) and is bundled into each script.

## Reporting a problem

Open an issue with your game version, the content of `Mods/ts4_unofficial_fixes.log`, and the output of `ufix.status`.

## License

[MIT](LICENSE). This project is not affiliated with or endorsed by Electronic Arts or Maxis.
