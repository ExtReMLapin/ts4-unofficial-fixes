FIX_ID = 'service_npc_offscreen'
# Fix: ServiceNpcService._fake_perform_services_if_necessary (service_npc_manager.py)
#
# When a lot loads, services that were scheduled while you were away (maid, gardener, ...)
# are "fake performed": paid and marked as done off-screen. A service that is still running
# at load time should be skipped so the NPC actually comes. EA checks that with
# `now + min_duration <= alarm_data.end_time`, but end_time is a time *of the week* while
# `now` is an absolute date, so after the first week of a save the check is always false.
# Result: you load during the maid's slot, you are billed, and the maid never shows up.
#
# The fix converts end_time to an absolute date in the same week as the service start.
# Everything else is EA's code, unchanged.

EXPECTED = '70e6b2b5dbb5e705'


def install():
    import sims4.log
    from date_and_time import DateAndTime, TimeSpan, sim_ticks_per_week
    from situations.service_npcs.service_npc_manager import ServiceNpcService

    logger = sims4.log.Logger('ServiceNPCManager')

    def _fake_perform_services_if_necessary(self, time_period_start, now):
        for scheduler in self._service_npc_requests:
            situation_creation_params = scheduler.extra_data
            household = situation_creation_params.hiring_household
            service_npc_type = situation_creation_params.service_npc_type
            service_record = household.get_service_npc_record(service_npc_type.guid64, add_if_no_record=False)
            if service_record is None:
                continue
            (time_until_service_arrives, alarm_data_entries) = scheduler.time_until_next_scheduled_event(time_period_start, schedule_immediate=True)
            if len(alarm_data_entries) != 1:
                logger.error('There are {} alarm data entries instead of 1 when fake performing services: {}', len(alarm_data_entries), alarm_data_entries, owner='bhill')
                continue
            alarm_data = alarm_data_entries[0]
            time_service_starts = time_period_start + time_until_service_arrives
            # --- fix: absolute end of the service window ---
            start_ticks = int(time_service_starts)
            week_start_ticks = start_ticks - start_ticks % sim_ticks_per_week()
            time_service_would_end = DateAndTime(week_start_ticks + int(alarm_data.end_time))
            # ------------------------------------------------
            min_service_duration = service_npc_type.min_duration_left_for_arrival_on_lot()
            if now < time_service_starts:
                continue
            if now + min_service_duration <= time_service_would_end:
                STATE.count('service_kept')
                continue
            if service_record.time_last_started_service is not None and service_record.time_last_started_service >= time_service_starts:
                continue
            service_npc_type.fake_perform(household)
            STATE.count('fake_performed')
            service_record.time_last_started_service = time_service_starts
            service_record.time_last_finished_service = min(now, time_service_would_end)
            if service_record.recurring:
                continue
            if service_npc_type.full_time_npc:
                continue
            if service_npc_type.max_work_duration() == TimeSpan.ZERO:
                continue
            self.cancel_service(household, service_npc_type)

    _replace(ServiceNpcService, '_fake_perform_services_if_necessary', _fake_perform_services_if_necessary, EXPECTED)


_run(install)
