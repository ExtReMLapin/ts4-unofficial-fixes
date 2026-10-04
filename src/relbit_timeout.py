FIX_ID = 'relbit_timeout'
# Fix: BitTimeoutData.load_bit_timeout (relationships/bit_timout.py)
#
# Timed relationship bits store the elapsed time when saved and restart their alarm with
# the remaining time when loaded. But the reload also resets the start time to "now", so the
# next save only records the time elapsed since the last load. Every save/load (and every
# lot travel, which saves sim data) makes the bit last longer than its tuned duration.
#
# Example with a 100 minute bit: saved at 60 -> reloaded with 40 left, start reset;
# saved again 30 minutes later -> stored elapsed = 30 instead of 90 -> reloaded with 70 left.
#
# The fix keeps EA's function and moves the start time back by the elapsed time it loaded.

EXPECTED = 'd83bae6398e829c1'


def install():
    import clock
    from date_and_time import DateAndTime
    from relationships.bit_timout import BitTimeoutData

    original = BitTimeoutData.__dict__['load_bit_timeout']

    def load_bit_timeout(self, time):
        result = original(self, time)
        if result and self._alarm_handle is not None:
            elapsed_ticks = int(clock.interval_in_sim_minutes(time).in_ticks())
            self._start_time = DateAndTime(int(self._start_time) - elapsed_ticks)
            STATE.count('timers_restored')
        return result

    _replace(BitTimeoutData, 'load_bit_timeout', load_bit_timeout, EXPECTED)


_run(install)
