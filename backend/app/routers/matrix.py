from fastapi import APIRouter, HTTPException

from app.cache import cache
from app.models import MatrixResponse

router = APIRouter(prefix="/matrix", tags=["matrix"])


@router.get("", response_model=MatrixResponse)
async def get_current_matrix() -> MatrixResponse:
    snapshot = await cache.get_snapshot()
    if snapshot is None:
        raise HTTPException(status_code=503, detail="Dashboard data is not loaded yet")
    if snapshot.current_milestone_id is None:
        raise HTTPException(status_code=404, detail="No milestone is available")
    return snapshot.matrices[snapshot.current_milestone_id]


@router.get("/{milestone_id}", response_model=MatrixResponse)
async def get_matrix(milestone_id: int) -> MatrixResponse:
    snapshot = await cache.get_snapshot()
    if snapshot is None:
        raise HTTPException(status_code=503, detail="Dashboard data is not loaded yet")
    matrix = snapshot.matrices.get(milestone_id)
    if matrix is None:
        raise HTTPException(status_code=404, detail="Milestone matrix was not found")
    return matrix

