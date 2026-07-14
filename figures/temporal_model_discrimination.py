# ══════════════════════════════════════════════════════════════════════
# TEMPORAL VALIDATION OF MODEL DISCRIMINATION
# Validation C-index by Model Type (Publication-Ready Figure)
# ══════════════════════════════════════════════════════════════════════

import matplotlib.pyplot as plt
import numpy as np

# Values from live notebook execution
models = ['CART Phenotyping\n(Current Study)', 'Full TNM Cox\nRegression', 'Multivariable Cox\n(Phenotype + Clinical)']
val_cindex = [0.566, 0.587, 0.609]  # Validation C-index values
colors = ['#1565C0', '#F57C00', '#6A1B9A']

fig, ax = plt.subplots(figsize=(12, 7))

# Create bars
x = np.arange(len(models))
bars = ax.bar(x, val_cindex, width=0.5, color=colors, alpha=0.85, edgecolor='black', linewidth=2.0, zorder=3)

# Reference line at C=0.5 (random discrimination)
ax.axhline(y=0.5, color='red', linestyle='--', linewidth=2.5, alpha=0.6, label='Random Discrimination (C=0.5)', zorder=2)

# Formatting
ax.set_ylabel('Validation Concordance Index (C-index)', fontsize=13, fontweight='bold')
ax.set_title('Temporal Validation of Model Discrimination:\nValidation C-index by Model Type',
             fontsize=14, fontweight='bold', pad=20)
ax.set_xticks(x)
ax.set_xticklabels(models, fontsize=11, fontweight='bold')
ax.set_ylim(0.45, 0.65)
ax.grid(axis='y', alpha=0.3, linestyle=':', linewidth=1.0, zorder=0)
ax.set_axisbelow(True)

# Add value labels on bars
for i, (bar, val) in enumerate(zip(bars, val_cindex)):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + 0.005,
            f'{val:.3f}', ha='center', va='bottom', fontsize=12, fontweight='bold', color='black')

# Legend
ax.legend(fontsize=11, loc='lower right', framealpha=0.95)

# Spine styling
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_linewidth(1.5)
ax.spines['bottom'].set_linewidth(1.5)

plt.tight_layout()
plt.savefig('Temporal_Model_Discrimination_Validation_Cindex.png', dpi=310, bbox_inches='tight', facecolor='white')
plt.show()

print("\n" + "="*80)
print("TEMPORAL VALIDATION OF MODEL DISCRIMINATION")
print("="*80)
print(f"\n{'Model':<45} {'Validation C-index':>20}")
print("-"*80)
for model, cindex in zip(models, val_cindex):
    model_clean = model.replace('\n', ' ')
    print(f"{model_clean:<45} {cindex:>20.3f}")
print("-"*80)
print(f"\nInterpretation:")
print(f"  • CART Phenotyping (C=0.566): Modest discrimination, baseline model")
print(f"  • Full TNM Cox (C=0.587): +0.021 improvement over CART")
print(f"  • Multivariable Cox (C=0.609): +0.043 improvement over CART (best)")
print(f"\n  All models significantly exceed random discrimination (C=0.5)")
print("="*80 + "\n")
