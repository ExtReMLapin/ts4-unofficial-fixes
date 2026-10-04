FIX_ID = 'narrative_loot_queue'
# Fix: NarrativeService.update (narrative/narrative_service.py)
#
# Narratives with "sim_info_loots" (loots given to every sim of the save) are queued and
# applied a few sims per tick. update() works on the first queued entry, but when that
# entry is finished it removes the *last* one with `.pop()`. With two entries queued, the
# second narrative's loots are dropped and never applied.
#
# The fix removes the entry that was actually finished (`.pop(0)`).

EXPECTED = '9fd42bf3a02ddeff'


def install():
    import time
    import services
    from event_testing.resolver import SingleSimResolver
    from narrative.narrative_service import NarrativeService

    def update(self):
        if self._pending_narrative_loots:
            persistence_service = services.get_persistence_service()
            (loots, _, sim_infos) = self._pending_narrative_loots[0]
            sim_info_manager = services.sim_info_manager()
            start_time = time.monotonic()
            while time.monotonic() - start_time < self.TIME_SLICE_SECONDS:
                if not sim_infos:
                    persistence_service.unlock_save(self)
                    self._pending_narrative_loots.pop(0)
                    if not self._pending_narrative_loots:
                        return
                    STATE.count('queued_narratives_applied')
                    (loots, _, sim_infos) = self._pending_narrative_loots[0]
                    persistence_service.lock_save(self)
                    continue
                sim_info = sim_infos.pop()
                if sim_info.sim_id in sim_info_manager and sim_info.can_instantiate_sim:
                    resolver = SingleSimResolver(sim_info)
                    for loot_action in loots:
                        loot_action.apply_to_resolver(resolver)

    _replace(NarrativeService, 'update', update, EXPECTED)


_run(install)
