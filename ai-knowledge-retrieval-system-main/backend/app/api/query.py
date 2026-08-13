from fastapi import APIRouter, HTTPException

from app.models.request_models import QueryRequest
from app.services.query_service import process_query

# Router for document query endpoints.
router = APIRouter(
    tags=["Query"],
)


# Process a user query using semantic search.
@router.post("/query")
def query_documents(request: QueryRequest):

    # Validate the number of requested results.
    if request.k < 1:
        raise HTTPException(
            status_code=400,
            detail="k must be at least 1",
        )

    # Delegate query processing to the service layer.
    return process_query(
        request.query,
        request.k,
    )