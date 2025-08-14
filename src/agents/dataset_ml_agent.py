"""DatasetMLAgent: Estimate project effort using data‑driven regression models.

This agent parses a tabular cost‑estimation dataset (e.g. ISBSG/COSMIC) and
builds predictive models to estimate effort.  It does not send a prompt to
the LLM – instead, it uses scikit‑learn locally.  The dataset path is read
from the environment variable ``DATASET_PATH``.  Supported file formats are
CSV and ARFF (attribute‑relation file format).  If the dataset or required
target column cannot be found, the agent returns an error message in the
result.

During analysis, the agent evaluates several regression algorithms (Random
Forest, Extra Trees, Gradient Boosting, and Linear Regression) with
cross‑validation.  Categorical features are label‑encoded per column and
missing numeric values are imputed with the column mean.  The agent reports
metrics for each candidate model, identifies the model with the lowest RMSE,
and surfaces the top features influencing the best model’s predictions.
"""

from __future__ import annotations

import os
import json
import math
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd
from scipy.io import arff  # type: ignore
from sklearn.ensemble import (
    RandomForestRegressor,
    ExtraTreesRegressor,
    GradientBoostingRegressor,
    IsolationForest,
)
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import KFold
from sklearn.metrics import mean_squared_error, mean_absolute_error
from sklearn.preprocessing import LabelEncoder

from .base_agent import BaseAgent


class DatasetMLAgent(BaseAgent):
    """A machine‑learning agent that builds an effort model from an external dataset."""

    def __init__(self, dataset_env_var: str = "DATASET_PATH") -> None:
        super().__init__("DatasetML")
        self.dataset_env_var = dataset_env_var

    def build_prompt(self, data: Dict[str, Any]) -> str:
        """This agent does not use an LLM, so no prompt is generated."""
        return ""

    def _load_dataset(self, path: str) -> Optional[pd.DataFrame]:
        """Load a dataset from CSV or ARFF into a DataFrame.

        :param path: Path to the dataset file.
        :return: DataFrame if successful, otherwise None.
        """
        try:
            ext = os.path.splitext(path)[1].lower()
            if ext == ".csv":
                return pd.read_csv(path)
            elif ext == ".arff":
                data, meta = arff.loadarff(path)
                df = pd.DataFrame(data)
                # decode bytes to strings for nominal features
                for col in df.columns:
                    if df[col].dtype == object:
                        df[col] = df[col].apply(lambda x: x.decode("utf-8") if isinstance(x, bytes) else x)
                return df
            else:
                return None
        except Exception:
            return None

    def _preprocess(self, df: pd.DataFrame, target_col: str) -> tuple[pd.DataFrame, pd.Series]:
        """Prepare feature matrix and target vector for modelling.

        Categorical columns are encoded using a separate LabelEncoder for each
        column.  Missing numeric values are imputed with the column mean.

        :param df: Raw DataFrame.
        :param target_col: Name of the effort column.
        :return: Tuple of (X, y).
        """
        df = df.copy()
        # Separate target
        y = df[target_col].astype(float)
        X = df.drop(columns=[target_col])
        # Encode categorical columns
        for col in X.columns:
            if X[col].dtype == object or X[col].dtype.name.startswith("category"):
                le = LabelEncoder()
                try:
                    X[col] = le.fit_transform(X[col])
                except Exception:
                    # replace problematic values with string representation then encode
                    X[col] = X[col].astype(str)
                    X[col] = le.fit_transform(X[col])
        # Impute missing numeric values
        for col in X.columns:
            if X[col].dtype != object:
                if X[col].isnull().any():
                    X[col] = X[col].fillna(X[col].mean())
        return X, y

    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Run training and evaluation on the dataset using multiple models.

        This method loads the dataset specified by the DATASET_PATH environment variable
        and evaluates several regression algorithms with cross‑validation.  It returns
        summary metrics for each candidate model and highlights the model with the
        lowest RMSE.

        :param data: Data dictionary (unused here).
        :return: Results dict with evaluation metrics or error message.
        """
        # Resolve dataset path from environment
        path = os.getenv(self.dataset_env_var)
        if not path:
            return {
                "agent": self.name,
                "_error": f"Environment variable {self.dataset_env_var} not set; cannot load dataset"
            }
        df = self._load_dataset(path)
        if df is None or df.empty:
            return {
                "agent": self.name,
                "_error": f"Failed to load dataset at {path} (supported formats: CSV, ARFF)"
            }
        # Identify target column (case‑insensitive search for 'effort')
        target_col = None
        for col in df.columns:
            if isinstance(col, str) and "effort" in col.lower():
                target_col = col
                break
        if target_col is None:
            return {
                "agent": self.name,
                "_error": "No effort column found in dataset; expected a column containing 'effort'"
            }
        X, y = self._preprocess(df, target_col)

        # Optional domain column for per‑domain calibration
        domain_col_name: Optional[str] = os.getenv("DOMAIN_COLUMN") or None
        if domain_col_name and domain_col_name not in df.columns:
            # Ignore if the requested domain column is not present
            domain_col_name = None
        # Validate features
        if X.shape[1] == 0:
            return {
                "agent": self.name,
                "_error": "Dataset has no usable features after preprocessing"
            }
        # Define candidate models (name, instance).  You can adjust parameters here for tuning.
        candidate_models: Dict[str, Any] = {
            "RandomForest_200": RandomForestRegressor(n_estimators=200, random_state=42),
            "RandomForest_500": RandomForestRegressor(n_estimators=500, random_state=42),
            "ExtraTrees_200": ExtraTreesRegressor(n_estimators=200, random_state=42),
            "GradientBoosting": GradientBoostingRegressor(random_state=42),
            "LinearRegression": LinearRegression(),
        }
        kf = KFold(n_splits=5, shuffle=True, random_state=42)
        model_results: Dict[str, Dict[str, Any]] = {}
        model_residuals: Dict[str, list[float]] = {}

        # Evaluate each model
        for name, model in candidate_models.items():
            rmses: list[float] = []
            maes: list[float] = []
            # Reset feature importance accumulator per model
            feature_importances = np.zeros(X.shape[1])
            residuals: list[float] = []
            for train_idx, test_idx in kf.split(X):
                X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
                y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
                # Some models require conversion to float32/float64
                try:
                    model.fit(X_train, y_train)
                except Exception:
                    # convert data types if model fails
                    model.fit(X_train.astype(float), y_train.astype(float))
                preds = model.predict(X_test)
                rmses.append(math.sqrt(mean_squared_error(y_test, preds)))
                maes.append(mean_absolute_error(y_test, preds))
                # track residuals for this model
                residuals.extend((y_test - preds).tolist())
                # Accumulate feature importances if available
                if hasattr(model, "feature_importances_"):
                    try:
                        feature_importances += model.feature_importances_
                    except Exception:
                        pass
            feature_importances /= kf.get_n_splits()
            # Store results
            model_results[name] = {
                "rmse": float(np.mean(rmses)),
                "mae": float(np.mean(maes)),
                "feature_importances": feature_importances.tolist(),
            }
            model_residuals[name] = residuals

        # Select best model (lowest RMSE)
        best_model_name = min(model_results.items(), key=lambda kv: kv[1]["rmse"])[0]
        best_model_info = model_results[best_model_name]
        # Determine top features from best model if feature importances exist
        importance_series = pd.Series(best_model_info["feature_importances"], index=X.columns)
        top_feats = importance_series.sort_values(ascending=False).head(5).to_dict()

        # Compute prediction interval for best model using residuals
        best_residuals = model_residuals.get(best_model_name, [])
        lower_quantile, upper_quantile = None, None
        if best_residuals:
            lower_quantile = float(np.quantile(best_residuals, 0.025))
            upper_quantile = float(np.quantile(best_residuals, 0.975))
        # Outlier detection using IsolationForest
        try:
            iso = IsolationForest(random_state=42, contamination='auto')
            # fit_predict returns 1 for inliers, -1 for outliers
            iso.fit(X)
            # Negative decision_function scores indicate outliers; lower values = more anomalous
            scores = -iso.decision_function(X)
            # Get top 5 outlier indices by score descending
            top_indices = np.argsort(scores)[-5:][::-1]
            outliers: list[Dict[str, Any]] = []
            for idx in top_indices:
                row_idx = int(idx)
                outliers.append({
                    "row_index": row_idx,
                    "score": float(scores[row_idx]),
                    "effort": float(y.iloc[row_idx]),
                    **({"domain": str(df.iloc[row_idx][domain_col_name])} if domain_col_name else {}),
                })
        except Exception:
            outliers = []

        # Domain‑specific model calibration
        domain_results: Dict[str, Any] = {}
        if domain_col_name:
            # iterate over each distinct domain value
            for dval in sorted(df[domain_col_name].dropna().unique()):
                try:
                    mask = df[domain_col_name] == dval
                    df_sub = df.loc[mask]
                    # Preprocess sub-data but drop domain column from features
                    # Ensure target exists
                    if df_sub.shape[0] < 5:
                        # skip small groups
                            continue
                    X_sub, y_sub = self._preprocess(df_sub, target_col)
                    if domain_col_name in X_sub.columns:
                        X_sub = X_sub.drop(columns=[domain_col_name])
                    # Evaluate candidate models on this subset
                    sub_results: Dict[str, Dict[str, Any]] = {}
                    for name, model in candidate_models.items():
                        rmses: list[float] = []
                        maes: list[float] = []
                        # Simple 3-fold CV to reduce time
                        sub_kf = KFold(n_splits=min(3, len(X_sub)), shuffle=True, random_state=42)
                        for tr_idx, te_idx in sub_kf.split(X_sub):
                            X_tr, X_te = X_sub.iloc[tr_idx], X_sub.iloc[te_idx]
                            y_tr, y_te = y_sub.iloc[tr_idx], y_sub.iloc[te_idx]
                            try:
                                model.fit(X_tr, y_tr)
                            except Exception:
                                model.fit(X_tr.astype(float), y_tr.astype(float))
                            preds = model.predict(X_te)
                            rmses.append(math.sqrt(mean_squared_error(y_te, preds)))
                            maes.append(mean_absolute_error(y_te, preds))
                        sub_results[name] = {
                            "rmse": float(np.mean(rmses)),
                            "mae": float(np.mean(maes)),
                        }
                    # Select best model for this domain
                    best_sub_name = min(sub_results.items(), key=lambda kv: kv[1]["rmse"])[0]
                    domain_results[str(dval)] = {
                        "best_model": best_sub_name,
                        "best_rmse": sub_results[best_sub_name]["rmse"],
                        "best_mae": sub_results[best_sub_name]["mae"],
                        "all_models": sub_results,
                        "count": int(df_sub.shape[0]),
                    }
                except Exception:
                    continue

        # Build response
        response: Dict[str, Any] = {
            "agent": self.name,
            "dataset_path": path,
            "target_column": target_col,
            "best_model": best_model_name,
            "best_model_rmse": best_model_info["rmse"],
            "best_model_mae": best_model_info["mae"],
            "top_features": {str(k): float(v) for k, v in top_feats.items()},
            "all_models": {
                m: {"rmse": float(info["rmse"]), "mae": float(info["mae"])}
                for m, info in model_results.items()
            },
        }
        # Attach prediction interval if computed
        if lower_quantile is not None and upper_quantile is not None:
            response["prediction_interval"] = {
                "lower_residual_quantile": lower_quantile,
                "upper_residual_quantile": upper_quantile,
                "interval_width": float(upper_quantile - lower_quantile),
            }
        if outliers:
            response["outliers"] = outliers
        if domain_results:
            response["domain_specific_models"] = domain_results
        return response