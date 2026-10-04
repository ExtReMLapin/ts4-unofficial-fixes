FIX_ID = 'organization_members'
# Fix: OrganizationService.generate_organization_members (organization_service.py)
#
# The function first filters the existing members of an organization, then is supposed to
# narrow them down with the blacklist and the event's extra filter terms. But the list it
# narrows is re-created empty right before the loop (`valid_org_member_ids = []` followed by
# `for org_member_id in valid_org_member_ids`), so existing members are never picked and
# every organization event (university societies, Eco Lifestyle / StrangerVille orgs, ...)
# recruits brand new NPCs, which are added to the member list each time.
#
# The fix runs that second pass over the cleaned member list, as intended.

EXPECTED = '114c38f7a43582d0'


def install():
    import random
    import services
    import sims4.resources
    from organizations.organization_service import OrganizationService

    def generate_organization_members(self, org_id, amount=0, blacklist_sims=(), additional_filter_terms=None, minimum=None):
        snippet_manager = services.get_instance_manager(sims4.resources.Types.SNIPPET)
        filter_service = services.sim_filter_service()
        sim_info_manager = services.sim_info_manager()
        if snippet_manager is None or filter_service is None or sim_info_manager is None:
            return []
        organization_snippet = snippet_manager.get(org_id)
        member_result_ids = self._organization_members.get(org_id)
        if member_result_ids is None:
            member_result_ids = []
        else:
            valid_org_member_ids = []
            invalid_org_member_ids = []
            for org_member_id in member_result_ids:
                if filter_service.does_sim_match_filter(org_member_id, sim_filter=organization_snippet.organization_filter, gsi_source_fn=lambda: str(self) + ': ' + str(organization_snippet)):
                    valid_org_member_ids.append(org_member_id)
                else:
                    invalid_org_member_ids.append(org_member_id)
            if invalid_org_member_ids:
                for invalid_org_member_id in invalid_org_member_ids:
                    invalid_org_member_info = sim_info_manager.get(invalid_org_member_id)
                    if invalid_org_member_info is not None and invalid_org_member_info.is_played_sim:
                        continue
                    member_result_ids.remove(invalid_org_member_id)
                    if invalid_org_member_info is None:
                        continue
                    organization_tracker = invalid_org_member_info.organization_tracker
                    if organization_tracker is not None:
                        organization_tracker.leave_organization(org_id)
            # --- fix: second pass over the existing members instead of an empty list ---
            candidate_ids = valid_org_member_ids
            valid_org_member_ids = []
            for org_member_id in candidate_ids:
            # ---------------------------------------------------------------------------
                if org_member_id not in blacklist_sims:
                    if filter_service.does_sim_match_filter(org_member_id, sim_filter=organization_snippet.organization_filter, additional_filter_terms=additional_filter_terms, gsi_source_fn=lambda: str(self) + ': ' + str(organization_snippet)):
                        valid_org_member_ids.append(org_member_id)
            if valid_org_member_ids:
                STATE.count('existing_members_reused', len(valid_org_member_ids))
            picked_sims = []
            if amount < len(valid_org_member_ids):
                while valid_org_member_ids and len(picked_sims) < amount:
                    random_choice = valid_org_member_ids.pop(random.randint(0, len(valid_org_member_ids) - 1))
                    picked_sims.append(random_choice)
                return picked_sims
            member_result_ids = valid_org_member_ids
        additional_membership_filter_terms = additional_filter_terms + OrganizationService.ADDITIONAL_FILTER_TERMS_ON_GENERATING_NEW_MEMBERS
        if minimum is not None and len(member_result_ids) <= minimum:
            members_needed = minimum - len(member_result_ids)
        else:
            members_needed = amount - len(member_result_ids)
        if members_needed > 0:
            new_members = filter_service.submit_matching_filter(number_of_sims_to_find=members_needed, sim_filter=organization_snippet.organization_filter, callback=None, allow_yielding=False, allow_instanced_sims=True, additional_filter_terms=additional_membership_filter_terms, blacklist_sim_ids=blacklist_sims, gsi_source_fn=lambda: str(self) + ': ' + str(organization_snippet))
            for new_member in new_members:
                sim_info = new_member.sim_info
                if sim_info:
                    if self.add_organization_member(sim_info, org_id):
                        member_result_ids.append(sim_info.id)
                        STATE.count('new_members_generated')
        return member_result_ids

    _replace(OrganizationService, 'generate_organization_members', generate_organization_members, EXPECTED)


_run(install)
