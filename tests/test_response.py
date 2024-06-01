from lapidary.runtime.model.op import _status_code_matches


def test__status_code_matches():
    matches = list(_status_code_matches('400'))
    assert ['400', '4XX', 'default'] == matches
