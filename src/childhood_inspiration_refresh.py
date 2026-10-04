FIX_ID = 'childhood_inspiration_refresh'
# Fix: SuggestedAspirationsManager.load (aspirations/suggested_aspirations_manager.py)
#
# Suggested childhood inspirations wait in a hidden queue and are moved to the visible slots
# by a repeating refresh alarm. That alarm is only created when something is added to an
# *empty* queue, and the queue is only emptied by the alarm itself. load() restores the
# queue from the save without creating the alarm, so after loading a save with queued
# inspirations, the visible slots are never refilled again.
#
# The fix re-arms the alarm after loading when the queue is not empty.

EXPECTED = '954c376833e43103'


def install():
    from aspirations.suggested_aspirations_manager import SuggestedAspirationsManager

    original = SuggestedAspirationsManager.__dict__['load']

    def load(self, msg):
        result = original(self, msg)
        if self._invisible_suggested_aspirations and self._refresh_suggested_aspiration_alarm_handle is None:
            self.add_refresh_alarm()
            STATE.count('alarms_rearmed')
        return result

    _replace(SuggestedAspirationsManager, 'load', load, EXPECTED)


_run(install)
