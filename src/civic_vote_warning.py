FIX_ID = 'civic_vote_warning'
# Fix: BaseCivicPolicyProviderServiceMixin._set_next_warn_alarm (civic_policies/base_civic_policy_provider.py)
#
# The "voting closes soon" warning is scheduled from `self._voting_close_time - now`.
# _voting_close_time is a time of the week (it is built with create_date_and_time(days=...)
# and the rest of the class reads it with now.time_to_week_time()), while `now` is an
# absolute date. From the second week of a save the result is negative and the warning
# alarm is never set.
#
# The fix measures the time until close the same way the rest of the class does.

EXPECTED = 'be46ea88171544cd'


def install():
    import alarms
    import services
    from date_and_time import TimeSpan
    from civic_policies.base_civic_policy_provider import BaseCivicPolicyProvider, BaseCivicPolicyProviderServiceMixin

    def _set_next_warn_alarm(self):
        if self._voting_warn_alarm is not None:
            alarms.cancel_alarm(self._voting_warn_alarm)
        if self._voting_close_time is None:
            return
        now = services.time_service().sim_now
        time_until_close = now.time_to_week_time(self._voting_close_time)
        time_until_warning = time_until_close - BaseCivicPolicyProvider.CIVIC_POLICY_SCHEDULE.voting_close_warning_duration()
        if TimeSpan.ZERO < time_until_warning:
            self._voting_warn_alarm = alarms.add_alarm(self, time_until_warning, lambda _: self._warn_voting(), cross_zone=True)
            STATE.count('warnings_scheduled')
        else:
            self._voting_warn_alarm = None

    _replace(BaseCivicPolicyProviderServiceMixin, '_set_next_warn_alarm', _set_next_warn_alarm, EXPECTED)


_run(install)
