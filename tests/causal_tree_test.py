import pytest

from . import _dgp
from ._common import validate_leaner, if_causal_tree_ready

_test_settings = {
    # data_generator: options
    _dgp.generate_data_x1b_y1_w0v5: dict(min_samples_leaf=3, max_depth=5),
    _dgp.generate_data_x2b_y1_w0v5: dict(min_samples_leaf=3, min_samples_split=3, max_depth=5),
    _dgp.generate_data_x1m_y1_w0v5: dict(min_samples_leaf=3, max_depth=5),
}


@if_causal_tree_ready
@pytest.mark.parametrize('dg', _test_settings.keys())
def test_causal_tree(dg):
    from why.estimator_model.causal_tree import CausalTree

    options = _test_settings[dg]
    dr = CausalTree(**options)
    validate_leaner(dg, dr, check_effect=True)
