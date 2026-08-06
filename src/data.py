"""
Data loading and preprocessing utilities for LiverMets analysis.
"""

import pandas as pd
import numpy as np
from pathlib import Path


def load_registry_data(filepath='LiverMets_Final_Dataset.csv'):
    """
    Load LiverMets registry dataset.

    Parameters
    ----------
    filepath : str, optional
        Path to the CSV file. Default: 'LiverMets_Final_Dataset.csv'

    Returns
    -------
    pd.DataFrame
        Loaded registry data

    Raises
    ------
    FileNotFoundError
        If the data file is not found
    """
    try:
        df = pd.read_csv(filepath)
        print(f"✓ Loaded: {len(df):,} patients × {df.shape[1]} variables")
        return df
    except FileNotFoundError:
        raise FileNotFoundError(f"Dataset not found: {filepath}")


def apply_inclusion_criteria(df):
    """
    Apply inclusion/exclusion criteria: complete TNM staging + survival data.

    Parameters
    ----------
    df : pd.DataFrame
        Raw registry data

    Returns
    -------
    tuple
        (included_df, excluded_df) with defined cohorts
    """
    # Complete TNM
    complete_tnm = df[
        (df['T_STAGE'].notna()) & (df['T_STAGE'] != 'ND') &
        (df['N_STAGE'].notna()) & (df['N_STAGE'] != 'ND') &
        (df['M_STAGE'].notna()) & (df['M_STAGE'] != 'ND')
    ].copy()

    # Complete survival
    included = complete_tnm[
        (complete_tnm['SURVIVAL_YEARS'].notna()) & (complete_tnm['SURVIVAL_YEARS'] > 0) &
        (complete_tnm['VITAL_STATUS'].notna())
    ].copy()

    excluded = df[~df.index.isin(included.index)].copy()

    return included, excluded


def define_phenotypes(df):
    """
    Define TNM-based phenotypes from CART analysis.

    Phenotype 1 (Favourable): M0, N0–N1
    Phenotype 2 (Intermediate): (M0, N2) OR (M1, N0–N1)
    Phenotype 3 (Adverse): M1, N2

    Parameters
    ----------
    df : pd.DataFrame
        Data with TNM columns

    Returns
    -------
    pd.DataFrame
        Data with new PHENOTYPE column
    """
    df = df.copy()
    df['PHENOTYPE'] = np.nan

    # Phenotype 1: M0, N0-N1
    mask1 = (df['M_STAGE'] == 'M0') & (df['N_STAGE'].isin(['N0', 'N1']))
    df.loc[mask1, 'PHENOTYPE'] = 1

    # Phenotype 2: (M0, N2) or (M1, N0-N1)
    mask2a = (df['M_STAGE'] == 'M0') & (df['N_STAGE'] == 'N2')
    mask2b = (df['M_STAGE'] == 'M1') & (df['N_STAGE'].isin(['N0', 'N1']))
    df.loc[mask2a | mask2b, 'PHENOTYPE'] = 2

    # Phenotype 3: M1, N2
    mask3 = (df['M_STAGE'] == 'M1') & (df['N_STAGE'] == 'N2')
    df.loc[mask3, 'PHENOTYPE'] = 3

    return df


def calculate_smd(x1, x2, binary=False):
    """
    Calculate standardized mean difference (SMD).

    Parameters
    ----------
    x1, x2 : array-like
        Two samples to compare
    binary : bool, optional
        If True, treat as binary proportions (default: False)

    Returns
    -------
    float
        Standardized mean difference
    """
    if binary:
        p1, p2 = x1, x2
        p_pool = (p1 + p2) / 2
        if p_pool == 0 or p_pool == 1:
            return 0
        pooled_sd = np.sqrt(p_pool * (1 - p_pool))
        return abs((p1 - p2) / pooled_sd) if pooled_sd > 0 else 0
    else:
        x1, x2 = np.asarray(x1), np.asarray(x2)
        m1, m2 = x1.mean(), x2.mean()
        pooled_sd = np.sqrt(
            ((len(x1) - 1) * x1.std()**2 + (len(x2) - 1) * x2.std()**2) /
            (len(x1) + len(x2) - 2)
        )
        return abs((m1 - m2) / pooled_sd) if pooled_sd > 0 else 0
