"""
Statistical analysis utilities for LiverMets study.

Includes: survival analysis, Cox regression, propensity score matching.
"""

import numpy as np
import pandas as pd
from scipy import stats


def kaplan_meier(time, event):
    """
    Compute Kaplan-Meier survival estimates.

    Parameters
    ----------
    time : array-like
        Follow-up time (years)
    event : array-like
        Event indicator (1=death, 0=censored)

    Returns
    -------
    dict
        Dictionary with 'time', 'survival', 'ci_lower', 'ci_upper'
    """
    # Sort by time
    idx = np.argsort(time)
    time_sorted = time.iloc[idx] if hasattr(time, 'iloc') else time[idx]
    event_sorted = event.iloc[idx] if hasattr(event, 'iloc') else event[idx]

    # Unique event times
    unique_times = np.unique(time_sorted[event_sorted == 1])

    km_survival = []
    km_time = []
    km_ci_lower = []
    km_ci_upper = []

    n_at_risk = len(time_sorted)
    cumulative_survival = 1.0

    for t in unique_times:
        n_events = sum((time_sorted == t) & (event_sorted == 1))
        n_at_risk_t = sum(time_sorted >= t)

        # KM estimator
        survival_t = cumulative_survival * (1 - n_events / n_at_risk_t)

        # Greenwood variance
        variance = cumulative_survival**2 * (n_events / (n_at_risk_t * (n_at_risk_t - n_events)))

        km_time.append(t)
        km_survival.append(survival_t)
        km_ci_lower.append(max(0, survival_t - 1.96 * np.sqrt(variance)))
        km_ci_upper.append(min(1, survival_t + 1.96 * np.sqrt(variance)))

        cumulative_survival = survival_t

    return {
        'time': np.array(km_time),
        'survival': np.array(km_survival),
        'ci_lower': np.array(km_ci_lower),
        'ci_upper': np.array(km_ci_upper),
    }


def propensity_score_matching(df, treatment_col, covariates, caliper=0.05, seed=42):
    """
    Perform one-to-one propensity score matching.

    Parameters
    ----------
    df : pd.DataFrame
        Data with treatment and covariates
    treatment_col : str
        Name of binary treatment column
    covariates : list
        List of covariate column names for propensity score model
    caliper : float, optional
        Caliper on propensity score scale (default: 0.05)
    seed : int, optional
        Random seed for reproducibility

    Returns
    -------
    dict
        Dictionary with 'matched_df', 'n_matched', 'n_unmatched'
    """
    from sklearn.linear_model import LogisticRegression
    from scipy.spatial.distance import cdist

    np.random.seed(seed)

    # Fit propensity score model
    X = df[covariates].fillna(df[covariates].mean())
    y = df[treatment_col].values

    lr = LogisticRegression(random_state=seed, max_iter=1000)
    lr.fit(X, y)
    ps = lr.predict_proba(X)[:, 1]

    # Separate treatment groups
    treated_idx = df[treatment_col] == 1
    control_idx = df[treatment_col] == 0

    treated_ps = ps[treated_idx]
    control_ps = ps[control_idx]

    treated_indices = np.where(treated_idx)[0]
    control_indices = np.where(control_idx)[0]

    # Match treated to control
    matched_treated = []
    matched_control = []

    for t_idx, t_ps in zip(treated_indices, treated_ps):
        distances = np.abs(control_ps - t_ps)
        closest_c_idx = control_indices[np.argmin(distances)]

        if distances[np.argmin(distances)] <= caliper:
            matched_treated.append(t_idx)
            matched_control.append(closest_c_idx)
            # Remove matched control
            control_ps = np.delete(control_ps, np.argmin(distances))
            control_indices = np.delete(control_indices, np.argmin(distances))

    matched_indices = np.concatenate([matched_treated, matched_control])
    matched_df = df.iloc[matched_indices].copy()

    return {
        'matched_df': matched_df,
        'n_matched': len(matched_treated),
        'n_unmatched_treated': treated_idx.sum() - len(matched_treated),
        'n_unmatched_control': control_idx.sum() - len(matched_control),
    }


def temporal_split(df, split_year=2009, year_col='REGISTRY_YEAR'):
    """
    Split data into training (≤split_year) and validation (>split_year) cohorts.

    Parameters
    ----------
    df : pd.DataFrame
        Data with year column
    split_year : int, optional
        Year to split on (default: 2009)
    year_col : str, optional
        Name of year column (default: 'REGISTRY_YEAR')

    Returns
    -------
    tuple
        (training_df, validation_df)
    """
    training = df[df[year_col] <= split_year].copy()
    validation = df[df[year_col] > split_year].copy()

    return training, validation
