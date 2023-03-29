from itertools import product

import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import r2_score
from sklearn.preprocessing import PolynomialFeatures

from why.estimator_model.double_ml import DoubleML
from why.exp_dataset.exp_data import single_continuous_treatment, single_binary_treatment
from . import _dgp
from ._common import validate_leaner

_test_settings = {
    # data_generator: (x_model,y_model )
    _dgp.generate_data_x1b_y1: (RandomForestClassifier(),
                                RandomForestRegressor(),
                                ),
    _dgp.generate_data_x1b_y2: (RandomForestClassifier(),
                                RandomForestRegressor(),
                                ),
    _dgp.generate_data_x1m_y1: (RandomForestClassifier(),
                                RandomForestRegressor(),
                                ),
    _dgp.generate_data_x2b_y1: (RandomForestClassifier(),
                                RandomForestRegressor(),
                                ),
    _dgp.generate_data_x2b_y2: (RandomForestClassifier(),
                                RandomForestRegressor(),
                                ),
    _dgp.generate_data_x2mb_y1: (RandomForestClassifier(),
                                 RandomForestRegressor(),
                                 ),
}


# _test_settings_to_be_fixed = {
#     # data_generator: (x_model,y_model )
#     _dgp.generate_data_x2b_y1: (RandomForestClassifier(),
#                                 RandomForestRegressor(),
#                                 ),
#     _dgp.generate_data_x2b_y2: (RandomForestClassifier(),
#                                 RandomForestRegressor(),
#                                 ),
# }

@pytest.mark.parametrize('dg', _test_settings.keys())
def test_double_ml(dg):
    x_model, y_model = _test_settings[dg]
    estimator = DoubleML(x_model=x_model, y_model=y_model, cf_fold=1, random_state=2022, is_discrete_treatment=True)
    validate_leaner(dg, estimator, check_effect_nji=True)


#
# @pytest.mark.parametrize('dg', _test_settings_to_be_fixed.keys())
# # @pytest.mark.xfail(reason='to be fixed')
# def test_double_ml_to_be_fixed(dg):
#     x_model, y_model = _test_settings_to_be_fixed[dg]
#     estimator = DoubleML(x_model=x_model, y_model=y_model, cf_fold=1, random_state=2022, is_discrete_treatment=True)
#     validate_leaner(dg, estimator, check_fitted=False)
#

########################################################################################

def exp_te(x):
    return np.exp(2 * x)


def test_dml_single_continuous_treatment():
    train, val, treatment_effect = single_continuous_treatment()
    adjustment = train.columns[:-4]
    covariate = 'c_0'
    outcome = 'outcome'
    treatment = 'treatment'

    dml = DoubleML(
        x_model=RandomForestRegressor(),
        y_model=RandomForestRegressor(),
        cf_fold=3,
    )
    dml.fit(
        train,
        outcome,
        treatment,
        adjustment,
        covariate,
    )
    dat = np.array(list(product(np.arange(0, 1, 0.01), repeat=1))).ravel()
    data_test = pd.DataFrame({'c_0': dat})
    true_te = np.array([exp_te(xi) for xi in data_test[covariate]])
    ested_te = dml.estimate(data_test).ravel()
    s = r2_score(true_te, ested_te)
    print(s)
    assert_single_continuous_treatment_estimation(dml, data_test[:3])


def test_dml_with_single_continuous_treatment_with_covariate_transformer():
    train, val, treatment_effect = single_continuous_treatment()
    adjustment = train.columns[:-4]
    covariate = 'c_0'
    outcome = 'outcome'
    treatment = 'treatment'

    dml = DoubleML(
        x_model=RandomForestRegressor(),
        y_model=RandomForestRegressor(),
        cf_fold=3,
        covariate_transformer=PolynomialFeatures(degree=3, include_bias=False)
    )
    dml.fit(
        train,
        outcome,
        treatment,
        adjustment,
        covariate,
    )
    dat = np.array(list(product(np.arange(0, 1, 0.01), repeat=1))).ravel()
    data_test = pd.DataFrame({'c_0': dat})
    true_te = np.array([exp_te(xi) for xi in data_test[covariate]])
    ested_te = dml.estimate(data_test).ravel()
    s = r2_score(true_te, ested_te)
    print(s)


def test_dml_single_binary_treatment():
    train1, val1, treatment_effect1 = single_binary_treatment()

    def exp_te(x): return np.exp(2 * x[0])

    n = 1000
    n_x = 4
    X_test1 = np.random.uniform(0, 1, size=(n, n_x))
    X_test1[:, 0] = np.linspace(0, 1, n)
    data_test_dict = {
        'c_0': X_test1[:, 0],
        'c_1': X_test1[:, 1],
        'c_2': X_test1[:, 2],
        'c_3': X_test1[:, 3],
    }
    data_test1 = pd.DataFrame(data_test_dict)
    true_te = np.array([exp_te(x_i) for x_i in X_test1])

    adjustment1 = train1.columns[:-7]
    covariate1 = train1.columns[-7:-3]
    # t_effect1 = train1['t_effect']
    treatment = 'treatment'
    outcome = 'outcome'
    dml1 = DoubleML(
        x_model=RandomForestClassifier(),
        y_model=RandomForestRegressor(),
        cf_fold=1,
        is_discrete_treatment=True,
    )
    dml1.fit(
        data=train1,
        outcome=outcome,
        treatment=treatment,
        adjustment=adjustment1,
        covariate=covariate1,
    )
    predicted = dml1.estimate(data_test1)
    assert_single_binary_treatment_estimation(dml1, data_test1)


def assert_single_continuous_treatment_estimation(dml_model, data_test):
    # numpy type
    ested_te_a:np.ndarray = dml_model.estimate(data_test, treat=np.ones((3))*2, control=np.ones((3)))
    ested_te_b:np.ndarray = dml_model.estimate(data_test, treat=np.ones((3))*3, control=np.ones((3)))
    ested_te_c:np.ndarray = dml_model.estimate(data_test, treat=np.ones((3))*2, control=np.ones((3)))
    assert (ested_te_a == ested_te_c).all()
    assert (ested_te_a != ested_te_b).any()

    # float type
    ested_te_e:np.ndarray = dml_model.estimate(data_test, treat=2.0, control=1.0)
    ested_te_f:np.ndarray = dml_model.estimate(data_test, treat=3.0, control=1.0)
    ested_te_g:np.ndarray = dml_model.estimate(data_test, treat=2.0, control=1.0)
    assert (ested_te_e == ested_te_g).all()
    assert (ested_te_e != ested_te_f).any()


def assert_single_binary_treatment_estimation(dml_model, data_test):
    #
    # numpy type
    # ested_te_a:np.ndarray = dml_model.estimate(data_test, treat=np.array([1,1]), control=np.array([0,0]))
    # ested_te_b:np.ndarray = dml_model.estimate(data_test, treat=np.array([2,2]), control=np.array([0,0]))
    # ested_te_c:np.ndarray = dml_model.estimate(data_test, treat=np.array([1,1]), control=np.array([0,0]))
    #
    # assert (ested_te_a == ested_te_c).all()
    # assert (ested_te_a != ested_te_b).any()

    # float type
    ested_te_e:np.ndarray = dml_model.estimate(data_test, treat=1, control=0)
    ested_te_f:np.ndarray = dml_model.estimate(data_test, treat=0, control=1)
    ested_te_g:np.ndarray = dml_model.estimate(data_test, treat=1, control=0)

    assert (ested_te_e == ested_te_g).all()
    assert (ested_te_e != ested_te_f).any()

