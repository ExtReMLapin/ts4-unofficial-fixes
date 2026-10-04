FIX_ID = 'situation_sim_data_prune'
# Fix: SituationManager._prune_sim_data (situations/situation_manager.py)
#
# The situation manager keeps per-sim data (mostly blacklist timers) and prunes the entries
# of sims that are gone and not blacklisted. The check is written `sim_data.is_blacklisted
# == False`, which compares the bound method itself to False (always unequal), so nothing is
# ever pruned and the table grows for the whole session.
#
# The fix calls the method.

EXPECTED = '6bec639550ae5b29'


def install():
    import services
    from objects import ALL_HIDDEN_REASONS
    from situations.situation_manager import SituationManager

    def _prune_sim_data(self):
        to_remove_ids = []
        for (sim_id, sim_data) in self._sim_data.items():
            sim_info = services.sim_info_manager().get(sim_id)
            if sim_info is not None and sim_info.is_instanced(allow_hidden_flags=ALL_HIDDEN_REASONS):
                continue
            if not sim_data.is_blacklisted():
                to_remove_ids.append(sim_id)
        for sim_id in to_remove_ids:
            del self._sim_data[sim_id]
        if to_remove_ids:
            STATE.count('entries_pruned', len(to_remove_ids))

    _replace(SituationManager, '_prune_sim_data', _prune_sim_data, EXPECTED)


_run(install)
