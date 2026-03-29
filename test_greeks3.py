# If Gamma is ~0.000147, it's very small because it's the sensitivity to a 1 point change in NIFTY which is a 20,000 index.
# Often gamma is reported multiplied by 100 or 10,000 depending on the platform? Or simply formatted with more decimals.
# Let's check other platforms. Gamma for index options is usually very small. Sometimes displayed as e.g., 0.0001 or 0.001. Or scaled by some amount.
# What are the standard display conventions for Gamma on Nifty? Usually just small decimals, but we only show 2 decimal places.

# If `fmt` is `v ? v.toFixed(2) : '-'`, then 0.000147 becomes 0.00. Wait, 0.000147 is falsy? No, it's truthy. So it becomes `0.00`.
# Is Gamma supposed to be multiplied by 100 like vega? Or just show more decimals? Or scaled by spot price?

# Another convention: Gamma is usually not multiplied by 100 in the formula. Wait, Delta is 0 to 1. Gamma is dDelta/dSpot. So for a 1 point move in Spot, Delta changes by 0.000147.
# Since Delta is 0 to 1, and Nifty moves by hundreds of points, a 100 point move changes delta by 0.0147.

# Let's see what the user says: "why is gamma 0? fix it"
