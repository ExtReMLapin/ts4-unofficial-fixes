FIX_ID = 'street_utility_venue_change'
# Fix: StreetUtilityShutoffEffect._on_venue_type_changed (civic_policies/street_civic_policy_effect.py)
#
# During a street utility shut-off (Eco Lifestyle), changing a residential lot to a venue
# type that should keep its utilities runs `del self._zone_ids_impacted[zone_id]`.
# _zone_ids_impacted is a list, so this raises an IndexError (zone ids are huge numbers)
# and the utilities of that lot are not turned back on.
#
# The fix removes the zone id from the list instead.

EXPECTED = '459e50aad11015d6'


def install():
    from civic_policies.street_civic_policy_effect import StreetUtilityShutoffEffect

    def _on_venue_type_changed(self, zone_id, active_venue_type):
        utility_can_be_shut_off = StreetUtilityShutoffEffect._should_have_utility_shut_off(active_venue_type)
        if zone_id in self._zone_ids_impacted:
            if not utility_can_be_shut_off:
                self._zone_ids_impacted.remove(zone_id)
                self._turn_on_utilities_for_zone(zone_id)
                STATE.count('utilities_restored')
        elif utility_can_be_shut_off:
            self._zone_ids_impacted.append(zone_id)
            self._turn_off_utilities_for_zone(zone_id)

    _replace(StreetUtilityShutoffEffect, '_on_venue_type_changed', _on_venue_type_changed, EXPECTED)


_run(install)
