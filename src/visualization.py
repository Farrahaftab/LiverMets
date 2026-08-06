"""
Visualization utilities for LiverMets survival and outcome plots.
"""

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


def set_publication_style():
    """Set matplotlib style for publication-quality figures."""
    sns.set_style("whitegrid")
    plt.rcParams['figure.figsize'] = (10, 6)
    plt.rcParams['font.size'] = 11
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['axes.labelsize'] = 12
    plt.rcParams['axes.titlesize'] = 13
    plt.rcParams['xtick.labelsize'] = 10
    plt.rcParams['ytick.labelsize'] = 10
    plt.rcParams['legend.fontsize'] = 10


def plot_kaplan_meier(ax, time, event, group=None, label=None, color='steelblue'):
    """
    Plot Kaplan-Meier survival curve.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Axes to plot on
    time : array-like
        Follow-up time (years)
    event : array-like
        Event indicator (1=death, 0=censored)
    group : array-like, optional
        Group labels for stratified curves
    label : str, optional
        Legend label
    color : str, optional
        Line color (default: 'steelblue')
    """
    from .analysis import kaplan_meier

    if group is None:
        km = kaplan_meier(time, event)
        ax.step(km['time'], km['survival'], where='post', label=label, color=color, linewidth=2)
        ax.fill_between(km['time'], km['ci_lower'], km['ci_upper'], step='post',
                        alpha=0.2, color=color)
    else:
        unique_groups = np.unique(group)
        colors = sns.color_palette("husl", len(unique_groups))

        for i, g in enumerate(unique_groups):
            mask = group == g
            km = kaplan_meier(time[mask], event[mask])
            ax.step(km['time'], km['survival'], where='post',
                   label=f"{label} = {g}" if label else f"Group {g}",
                   color=colors[i], linewidth=2)
            ax.fill_between(km['time'], km['ci_lower'], km['ci_upper'], step='post',
                           alpha=0.2, color=colors[i])

    ax.set_xlabel('Follow-up (years)')
    ax.set_ylabel('Survival probability')
    ax.set_ylim([0, 1.05])
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)


def plot_forest(ax, estimates, ci_lower, ci_upper, labels=None, vline_x=1.0):
    """
    Plot forest plot for hazard ratios or odds ratios.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Axes to plot on
    estimates : array-like
        Point estimates (e.g., HR)
    ci_lower : array-like
        Lower confidence interval bounds
    ci_upper : array-like
        Upper confidence interval bounds
    labels : list, optional
        Variable labels for y-axis
    vline_x : float, optional
        Vertical line position (default: 1.0 for HR)
    """
    y_pos = np.arange(len(estimates))

    ax.scatter(estimates, y_pos, s=100, color='darkblue', zorder=3)
    ax.hlines(y_pos, ci_lower, ci_upper, colors='darkblue', linewidth=2)
    ax.axvline(vline_x, color='red', linestyle='--', linewidth=1, alpha=0.7)

    ax.set_yticks(y_pos)
    if labels:
        ax.set_yticklabels(labels)
    ax.set_xlabel('Hazard Ratio (log scale)')
    ax.set_xscale('log')
    ax.grid(True, alpha=0.3, axis='x')


def plot_phenotype_distribution(ax, phenotype_counts, phenotype_labels=None):
    """
    Plot distribution of patients by phenotype.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Axes to plot on
    phenotype_counts : array-like
        Count of patients in each phenotype
    phenotype_labels : list, optional
        Labels for phenotypes
    """
    if phenotype_labels is None:
        phenotype_labels = ['Favourable', 'Intermediate', 'Adverse']

    colors = sns.color_palette("Set2", len(phenotype_counts))
    bars = ax.bar(phenotype_labels, phenotype_counts, color=colors, edgecolor='black')

    # Add count labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2., height,
               f'{int(height):,}',
               ha='center', va='bottom', fontsize=11)

    ax.set_ylabel('Number of patients')
    ax.set_ylim([0, max(phenotype_counts) * 1.1])
    ax.grid(True, alpha=0.3, axis='y')
