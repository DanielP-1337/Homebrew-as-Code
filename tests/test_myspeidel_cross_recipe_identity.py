"""Fail-closed offline tests for cross-recipe identity corroboration."""
import pytest
from homebrew_as_code.myspeidel_cross_recipe_identity import analyze_pairs


def pair(uuid, web_id='6333', cloud_uuid='cloud-a', *, count=1, name_equal=True, status='CANDIDATE'):
    return {'recipe_uuid': uuid, 'mapping_report': {
        'name_equal': name_equal, 'web_occurrence_count': count,
        'cloud_occurrence_count': count, 'mappings': [
            {'web_group': 'hops_to_recipe', 'web_id': web_id,
             'status': status, 'candidate_cloud_uuids': [cloud_uuid]}
            for _ in range(count)]}}


def item(*pairs):
    return analyze_pairs(list(pairs))['identities'][0]


def test_single_recipe_is_not_cross_recipe_evidence():
    assert item(pair('uuid1', count=2))['status'] == 'SINGLE_RECIPE_CANDIDATE'


def test_distinct_recipes_corroborate_but_do_not_verify():
    report = analyze_pairs([pair('uuid1', count=2), pair('uuid2')])
    assert report['identities'][0]['status'] == 'CROSS_RECIPE_CORROBORATED'
    assert report['identities'][0]['distinct_eligible_recipes'] == 2
    assert report['verified_mapping_count'] == 0


def test_conflicting_cloud_uuids_are_explicit():
    assert item(pair('uuid1'), pair('uuid2', cloud_uuid='cloud-b'))['status'] == 'CONFLICT'


def test_unresolved_second_recipe_blocks_corroboration():
    assert item(pair('uuid1'), pair('uuid2', status='UNRESOLVED', cloud_uuid='cloud-b'))['status'] == 'AMBIGUOUS_OR_INCOMPLETE'


def test_bad_name_prevents_corroboration():
    assert item(pair('uuid1'), pair('uuid2', name_equal=False))['status'] == 'SINGLE_RECIPE_CANDIDATE'


def test_duplicate_uuid_is_not_independent_recipe():
    with pytest.raises(ValueError, match='distinct UUID'):
        analyze_pairs([pair('uuid1'), pair('uuid1')])


def test_same_web_id_different_uuid_within_recipe_not_counted():
    p = pair('uuid1')
    p['mapping_report']['mappings'].append({'web_group': 'hops_to_recipe', 'web_id': '6333',
                                            'status': 'CANDIDATE', 'candidate_cloud_uuids': ['cloud-b']})
    p['mapping_report']['web_occurrence_count'] = 2
    p['mapping_report']['cloud_occurrence_count'] = 2
    assert item(p, pair('uuid2'))['status'] == 'AMBIGUOUS_OR_INCOMPLETE'


def test_reject_invalid_candidate_shape():
    p = pair('uuid1')
    p['mapping_report']['mappings'][0]['candidate_cloud_uuids'] = 'cloud-a'
    with pytest.raises(ValueError, match='candidate UUID'):
        analyze_pairs([p])
