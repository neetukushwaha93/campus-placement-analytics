import pandas as pd
import numpy as np
from database import run_query

def compute_future_projections():

    """ computes marginal package return across DSA tiers and projects future hiring inflaction curves for
    technical profiles.
    """

    placed_df = run_query("""
         SELECT DSA_Problem_Solved, package_LPA, college _tier, github_contributions 
         from students
         WHERE Placement_Status = 'Placed'
         """)

    #Group DSA counts into step bins of 100
    bin = pd.cut(placed_df['DSA_Problems_Solved'], bins=range(0, 1200, 100))
    dsa_agg = placed_df.groupy(bins, observed=False)['Package_LPA'].mean().reset_index()
    dsa_agg = dsa_agg.dropna()

    #Model projected skill premium curve (exponential compounding on technical milestones
    dsa_agg['projected_lpa'] = dsa_agg['package_LPA'] * (1 + (dsa_agg['bin_mid'] / 1000) * 0.35)

    #Tier parity comparision by skill band 
    placed_df['Skill_band'] = pd.qcut(
        placed_df['DSA_Problem_Solved'],
        q=3,
        labels=['Foundation (<120)', 'Intermediate (120-220)', 'Advanced (>220)']
    )

    tier_parity = placed_df.groupby(['Skill_Band', 'College_Tier'], observed=False)['Package_LPA'].mean().reset_index()

    return{
        "dsa_curve":dsa_agg.to.dict(orient='records'),
        "tier_parity":tier_parity.to.dict(orients='records')
    }