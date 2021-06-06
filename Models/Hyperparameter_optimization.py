from skopt import dump
from skopt.callbacks import DeltaXStopper
from skopt.space import Integer, Real, Categorical
from skopt.utils import use_named_args
from skopt import gp_minimize, forest_minimize
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import Pipeline
import os

# define the space of hyperparameters to search
SPACE = {
    "LogisticRegression": [
        # Categorical(['none', 'l2'], name='penalty'),
        Real(1e-6, 100.0, 'log-uniform', name='tol'),
        Real(1e-6, 100.0, 'log-uniform', name='C'),
        Categorical([True, False], name='fit_intercept'),
        # Real(-5, 5, 'log-uniform', name='intercept_scaling'),
        Categorical(['newton-cg', 'lbfgs', 'sag', 'saga'], name='solver'),
        Categorical(['auto', 'ovr', 'multinomial'], name='multi_class'),
        Integer(100, 200, name='max_iter'),
        Integer(0, 50, name='random_state'),
        # Integer(0, 100, name='verbose')
    ],
    "RandomForestClassifier": [
        Integer(100, 700, name='n_estimators'),
        Categorical(['gini', 'entropy'], name='criterion'),
        Integer(1, 30, name='max_depth'),
        Categorical(['auto', 'sqrt', 'log2'], name='max_features'),
        # Categorical([True, False], name='bootstrap'),
        Categorical([True, False], name='oob_score'),
    ],
    "MLPClassifier": [
        Categorical(['identity', 'logistic', 'tanh', 'relu'], name='activation'),
        Categorical(['lbfgs', 'sgd', 'adam'], name='solver'),
        Categorical(['constant', 'invscaling', 'adaptive'], name='learning_rate'),
        Integer(100, 500, name='max_iter'),
        Real(1e-6, 100.0, 'log-uniform', name='tol'),
        Real(1e-8, 100.0, 'log-uniform', name='epsilon'),
    ],
    "XGBClassifier": [
        Integer(1, 18, name='max_depth'),
        Integer(1, 9, name='gamma'),
        Integer(40, 180, name='reg_alpha'),
        Real(0, 1.0, name='reg_lambda'),
        Real(0.5, 1.0, name='colsample_bytree'),
        Integer(0, 10, name='min_child_weight'),
        Integer(0, 180, name='n_estimators'),
    ],
    "QuadraticDiscriminantAnalysis": [
        Real(0, 1, name='reg_param')
    ],
    "SVC": [
        Real(0, 100, name='C'),
        Real(0.001, 1, name='gamma'),
        Categorical(['rbf', 'poly', 'sigmoid'], name='kernel')
    ],
    'LinearDiscriminantAnalysis': [
        Categorical(['lsqr', 'eigen'], name='solver'),
        Real(0, 1, name='shrinkage')
]
}


# SPACE =
#     [
#     Real(0.01, 0.5, name='learning_rate', prior='log-uniform'),
#     Integer(1, 30, name='max_depth'),
#     Integer(100, 700, name='n_estimators'),
#     Integer(0, 1, name='n_components'),
#     Integer(100, 200, name='max_iter'),
#     Integer(2, 100, name='num_leaves'),
#     Integer(10, 1000, name='min_data_in_leaf'),
#     Real(0.1, 1.0, name='feature_fraction', prior='uniform'),
#     Real(0.1, 1.0, name='subsample', prior='uniform'),
#     Real(1e-6, 100.0, 'log-uniform', name='C'),
#     Categorical(['linear', 'poly', 'rbf', 'sigmoid'], name='kernel'),
#     # Categorical(['svd', 'lsqr', 'eigen'], name='solver'),
#     Integer(1, 5, name='degree'),
#     Real(1e-6, 100.0, 'log-uniform', name='gamma'),
#     Real(0, 1, name='reg_param')
# ]


def evaluate_hyperparameter(model, X_train, X_val, y_train, y_val):
    classifier = model["classifier"] if type(model) == Pipeline else model

    filter_space = SPACE[type(
        classifier).__name__]  # [p for p in SPACE[type(classifier).__name__] if p.name in classifier.get_params().keys()]

    # define the function used to evaluate a given configuration
    @use_named_args(filter_space)
    def evaluate_model(**params):
        # configure the model with specific hyperparameters
        if type(model) == Pipeline:
            model["classifier"].set_params(**params)
        else:
            model.set_params(**params)
        model.fit(X_train, y_train)
        y_pred = model.predict_proba(X_val)[:, 1]
        return roc_auc_score(y_val, y_pred)

    # perform optimization
    results = forest_minimize(evaluate_model, filter_space, callback=DeltaXStopper(1e-2))

    # save the results
    directory = 'artifacts'
    file_name = '%s_results.pkl' % type(classifier).__name__

    if not os.path.exists(directory):
        os.makedirs(directory)

    with open(os.path.join(directory, file_name), 'wb') as file:
        dump(results, file, store_objective=False)

    # summarizing finding:
    dictionary = dict(zip([p.name for p in filter_space], results.x))
    print('Accuracy achieved with the validation set: %.3f' % results.fun)
    print('Best Parameters: %s' % dictionary)
    return dictionary
