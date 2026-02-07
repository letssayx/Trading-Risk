from fastapi import APIRouter, Depends, HTTPException
from typing import List
from backend.auth.service import AuthService # Using authentication dependency
from backend.domain.market.registry import MarketRegistry
from backend.domain.market.schemas import InstrumentSchema

router = APIRouter(prefix="/api/search", tags=["Universal Search"])

# Dependency to get Registry
def get_registry():
    return MarketRegistry()

@router.get("/", response_model=List[InstrumentSchema])
async def search_instruments(query: str, registry: MarketRegistry = Depends(get_registry)):
    """
    Universal search endpoint for finding instruments across asset classes.
    """
    if len(query) < 2:
        return []

    results = registry.search_instruments(query)

    # Mocking extended results for "Universal Search" demo
    if "GOLD" in query.upper():
        results.append(InstrumentSchema(
            turtle_id="MCX_GOLD_FUT",
            symbol="GOLD",
            exchange="MCX",
            exchange_mapping={"MCX": "GOLDM24"},
            details={"asset_class": "Commodity"}
        ))
    if "CORN" in query.upper():
        results.append(InstrumentSchema(
            turtle_id="CBOT_CORN_FUT",
            symbol="ZC",
            exchange="CBOT",
            exchange_mapping={"CBOT": "ZCZ3"},
            details={"asset_class": "Commodity"}
        ))

    return results
