from fastapi import APIRouter, HTTPException
from typing import Dict, Optional, List, Any
import pandas as pd
import numpy as np

# Strategies
from backend.strategies.turtle import TurtleLegacyStrategy
from backend.strategies.convergence import check_convergence
from backend.strategies.risk import get_risk_dashboard_data
from backend.strategies.macro_stat_arb import calculate_pca_factors
from backend.strategies.vol_arb import calculate_vol_spread

# Analysis & Intelligence
from backend.intelligence.sentiment_flow import analyze_sentiment_flow
from backend.analysis.beta import calculate_beta
from backend.risk.hedging import calculate_index_hedge, calculate_sentiment_hedge

# Schemas (Refactored Location)
from backend.api.schemas import (
    StrategyRequest, SentimentRequest, ConvergenceRequest,
    VolArbRequest, PCARequest
)

router = APIRouter(prefix="/strategies", tags=["Consolidated Strategies"])

# --- Endpoints ---

@router.post("/sentiment/analyze")
def sentiment_analysis(req: SentimentRequest):
    signal = analyze_sentiment_flow(req.fii_net, req.pcr, req.trin, req.price_chg, req.oi_chg)
    return {"signal": signal}

@router.post("/convergence/check")
def convergence_check(req: ConvergenceRequest):
    res = check_convergence(req.turtle_signal, req.sentiment_signal)
    return res

@router.post("/vol-arb/calendar")
def vol_arb_check(req: VolArbRequest):
    res = calculate_vol_spread(req.iv_near, req.iv_far)
    return res

@router.post("/macro/pca")
def run_pca(req: PCARequest):
    # Convert list to DataFrame
    df = pd.DataFrame(req.returns_matrix)
    res = calculate_pca_factors(df)
    # Simplify for JSON (factors might be large)
    return {
        "eigenvalues": res["eigenvalues"],
        "explained_variance": res["explained_variance"]
    }

@router.get("/toolbox/registry")
def get_toolbox_registry():
    from backend.infrastructure.registry import ToolboxRegistry
    ToolboxRegistry.auto_discover()
    return {"tools": ToolboxRegistry.get_widgets()}
