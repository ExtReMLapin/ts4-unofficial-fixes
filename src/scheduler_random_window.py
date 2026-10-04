FIX_ID = 'scheduler_random_window'
# Fix: WeeklySchedule._alarm_callback (scheduler.py)
#
# For schedule entries with a random start, EA computes the remaining time of the window as
# `alarm_data.end_time - now.time_since_beginning_of_week()` and feeds it to random.randint.
# When the alarm fires after the end of its window (typically while a lot is loading) the
# value is negative: randint raises "empty range for randrange()", the exception escapes
# before schedule_next_alarm() and that schedule never fires again for the session.
# When the window wraps past the end of the week (e.g. Saturday 22:00 -> Sunday 02:00) the
# value is a full week too large and the random start can be pushed a week later.
#
# The fix keeps EA's logic and only clamps that value into the window.

EXPECTED = '3750551e8cdee20e'


def install():
    import functools
    import random
    import alarms
    import services
    from date_and_time import TimeSpan, sim_ticks_per_week
    from scheduler import WeeklySchedule

    def _alarm_callback(self, handle, alarm_datas=None):
        if alarm_datas is None:
            alarm_datas = self._alarm_data.pop(self._alarm_handle)
            self._alarm_handle = None
        if self._start_callback is not None:
            for alarm_data in alarm_datas:
                if alarm_data.is_random:
                    current_time = services.time_service().sim_now
                    current_time = current_time.time_since_beginning_of_week()
                    available_ticks = (alarm_data.end_time - current_time).in_ticks()
                    week_ticks = sim_ticks_per_week()
                    if available_ticks > week_ticks:
                        # window wraps past the end of the week and we are after midnight
                        available_ticks -= week_ticks
                        STATE.count('week_wrap')
                    if available_ticks < 0:
                        # alarm fired after its window: start now instead of crashing
                        available_ticks = 0
                        STATE.count('late_alarm')
                    random_time_span = TimeSpan(random.randint(0, int(available_ticks)))
                    random_callback = functools.partial(self._random_alarm_callback, alarm_data=alarm_data)
                    cur_handle = alarms.add_alarm(self, random_time_span, random_callback, cross_zone=self._cross_zone)
                    self._random_alarm_handles.append(cur_handle)
                else:
                    self._start_callback(self, alarm_data, self.extra_data)
        self.schedule_next_alarm(schedule_immediate=False)

    _replace(WeeklySchedule, '_alarm_callback', _alarm_callback, EXPECTED)


_run(install)
