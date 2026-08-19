from fastapi import APIRouter, HTTPException

from app.models.request_models import QueryRequest
from app.orchestration.workflow import run_workflow


router = APIRouter(
    tags=["Query"],
)


@router.post(
    "/query",
    summary="Query Documents",
    description=(
        "Run the complete Milestone 2 LangGraph workflow.\n\n"
        "Flow: "
        "FastAPI → LangGraph Workflow → Query Understanding → "
        "Query Routing → Retrieval → Response Generation → "
        "Final Response"
    ),
)
def query_documents(
    request: QueryRequest,
):
    """
    Run the complete Milestone 2 LangGraph workflow.

    Flow:
        FastAPI
        ->
        LangGraph Workflow
        ->
        Query Understanding
        ->
        Query Routing
        ->
        Retrieval
        ->
        Response Generation
        ->
        Final Response
    """

    # -------------------------------------------------------------
    # Validate request
    # -------------------------------------------------------------

    if request.k < 1:
        raise HTTPException(
            status_code=400,
            detail="k must be at least 1",
        )

    try:
        # ---------------------------------------------------------
        # Run the complete LangGraph workflow
        # ---------------------------------------------------------

        result = run_workflow(
            query=request.query,
            k=request.k,
        )

        # ---------------------------------------------------------
        # Handle workflow-level errors
        # ---------------------------------------------------------

        if result.get("error"):
            raise HTTPException(
                status_code=500,
                detail=result["error"],
            )

        # ---------------------------------------------------------
        # Extract Query Understanding result
        # ---------------------------------------------------------

        query_analysis = result.get(
            "query_analysis"
        )

        query_understanding = None

        if query_analysis is not None:
            query_understanding = (
                query_analysis.model_dump()
            )

        # ---------------------------------------------------------
        # Return final Milestone 2 response
        # ---------------------------------------------------------

        return {
            "success": True,
            "query": request.query,
            "query_understanding": query_understanding,
            "route": result.get("route"),
            "route_reason": result.get("route_reason"),
            "retrieval": result.get("retrieval_result"),
            "response": result.get("response"),
        }

    except HTTPException:
        raise

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Query processing failed: {error}"
            ),
        )