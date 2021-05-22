from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler
import numpy as np

from Models.Hyperparameter_optimization import evaluate_hyperparameter
from Models.utils import read_data, split_train_test, plot_roc_curve


def main():
    pipeline = Pipeline([
        ("scaler", MinMaxScaler()),
        ("classifier", LogisticRegression())
    ])

    dataset = read_data()

    X_train, X_val, X_test, y_train, y_val, y_test = split_train_test(dataset)

    params = evaluate_hyperparameter(LogisticRegression(), X_train, X_val, y_train, y_val)

    model = LogisticRegression(**params)
    model.fit(np.row_stack([X_train, X_val]), np.concatenate([y_train, y_val]))
    y_pred = model.predict_proba(X_test)[:, 1]

    plot_roc_curve(y_test, y_pred)


if __name__ == "__main__":
    main()