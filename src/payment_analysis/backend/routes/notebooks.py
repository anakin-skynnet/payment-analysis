"""
Notebook Registry - Maps UI sections to Databricks notebooks.

This module provides a centralized registry of all Databricks notebooks
used in the payment analysis platform, organized by functional area.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(tags=["notebooks"])


# =============================================================================
# Models
# =============================================================================

class NotebookCategory(str, Enum):
    """Notebook categories."""
    INTELLIGENCE = "intelligence"
    ML_TRAINING = "ml_training"
    STREAMING = "streaming"
    TRANSFORMATION = "transformation"
    ANALYTICS = "analytics"


class NotebookInfo(BaseModel):
    """Notebook metadata model."""
    id: str = Field(..., description="Unique notebook identifier")
    name: str = Field(..., description="Notebook display name")
    description: str = Field(..., description="Notebook purpose and functionality")
    category: NotebookCategory = Field(..., description="Functional category")
    workspace_path: str = Field(..., description="Databricks workspace path")
    job_name: str | None = Field(None, description="Associated job name if scheduled")
    tags: list[str] = Field(default_factory=list, description="Searchable tags")
    documentation_url: str | None = Field(None, description="Link to documentation")


class NotebookList(BaseModel):
    """List of notebooks."""
    notebooks: list[NotebookInfo]
    total: int
    by_category: dict[str, int]


# =============================================================================
# Notebook Registry
# =============================================================================

NOTEBOOKS = [
    # Intelligence Layer
    NotebookInfo(
        id="agent_framework",
        name="Intelligence Results Framework",
        description="SQL-based intelligent decisioning system for smart routing, retry optimization, decline analysis, risk assessment, and performance recommendations.",
        category=NotebookCategory.INTELLIGENCE,
        workspace_path="/Workspace/Users/ariel.hdez@databricks.com/getnet_approval_rates_v2/files/src/payment_analysis/agents/agent_framework.py",
        job_name="Smart Routing, Smart Retry, Decline Analysis, Risk Assessment, Performance Recommendations",
        tags=["intelligence", "decisioning", "routing", "retry", "analysis"],
    ),
    
    # ML Training
    NotebookInfo(
        id="train_models",
        name="ML Model Training",
        description="Trains all 4 ML models: approval propensity, risk scoring, smart routing policy, and smart retry policy with MLflow tracking.",
        category=NotebookCategory.ML_TRAINING,
        workspace_path="/Workspace/Users/ariel.hdez@databricks.com/getnet_approval_rates_v2/files/src/payment_analysis/ml/train_models.py",
        job_name="Train Payment Approval ML Models",
        tags=["ml", "training", "mlflow", "models", "propensity", "risk"],
    ),
    
    # Streaming & Ingestion
    NotebookInfo(
        id="transaction_simulator",
        name="Transaction Stream Simulator",
        description="Generates realistic synthetic payment transaction events for testing and demonstration purposes.",
        category=NotebookCategory.STREAMING,
        workspace_path="/Workspace/Users/ariel.hdez@databricks.com/getnet_approval_rates_v2/files/src/payment_analysis/streaming/transaction_simulator.py",
        job_name="Payment Transaction Stream Simulator",
        tags=["streaming", "simulator", "synthetic-data", "testing"],
    ),
    NotebookInfo(
        id="bronze_ingest",
        name="Bronze Layer Ingestion",
        description="Delta Live Tables pipeline for ingesting raw payment events into the bronze layer with data quality checks.",
        category=NotebookCategory.STREAMING,
        workspace_path="/Workspace/Users/ariel.hdez@databricks.com/getnet_approval_rates_v2/files/src/payment_analysis/streaming/bronze_ingest.py",
        job_name="Payment Analysis DLT Pipeline",
        tags=["dlt", "bronze", "ingestion", "data-quality"],
    ),
    NotebookInfo(
        id="realtime_pipeline",
        name="Real-Time Streaming Pipeline",
        description="Delta Live Tables continuous streaming pipeline for real-time payment processing (Bronze → Silver → Gold).",
        category=NotebookCategory.STREAMING,
        workspace_path="/Workspace/Users/ariel.hdez@databricks.com/getnet_approval_rates_v2/files/src/payment_analysis/streaming/realtime_pipeline.py",
        job_name="Payment Analysis DLT Pipeline",
        tags=["dlt", "streaming", "realtime", "cdc", "continuous"],
    ),
    NotebookInfo(
        id="continuous_processor",
        name="Continuous Stream Processor",
        description="Structured streaming processor for continuous payment event processing with windowed aggregations.",
        category=NotebookCategory.STREAMING,
        workspace_path="/Workspace/Users/ariel.hdez@databricks.com/getnet_approval_rates_v2/files/src/payment_analysis/streaming/continuous_processor.py",
        job_name=None,
        tags=["streaming", "continuous", "aggregations", "windows"],
    ),
    
    # Transformations
    NotebookInfo(
        id="silver_transform",
        name="Silver Layer Transformations",
        description="Delta Live Tables transformations for cleaning, enriching, and validating payment data in the silver layer.",
        category=NotebookCategory.TRANSFORMATION,
        workspace_path="/Workspace/Users/ariel.hdez@databricks.com/getnet_approval_rates_v2/files/src/payment_analysis/transform/silver_transform.py",
        job_name="Payment Analysis DLT Pipeline",
        tags=["dlt", "silver", "transformation", "enrichment", "validation"],
    ),
    NotebookInfo(
        id="gold_views",
        name="Gold Analytics Views",
        description="Creates aggregated gold-layer views optimized for dashboards and analytics (12+ views including KPIs, trends, and performance metrics).",
        category=NotebookCategory.TRANSFORMATION,
        workspace_path="/Workspace/Users/ariel.hdez@databricks.com/getnet_approval_rates_v2/files/src/payment_analysis/transform/gold_views.py",
        job_name="Create Payment Analysis Gold Views",
        tags=["dlt", "gold", "views", "aggregations", "analytics"],
    ),
    NotebookInfo(
        id="gold_views_sql",
        name="Gold Views SQL Definitions",
        description="SQL definitions for all gold-layer analytics views (v_executive_kpis, v_decline_patterns, v_routing_performance, etc.).",
        category=NotebookCategory.TRANSFORMATION,
        workspace_path="/Workspace/Users/ariel.hdez@databricks.com/getnet_approval_rates_v2/files/src/payment_analysis/transform/gold_views.sql",
        job_name="Create Payment Analysis Gold Views",
        tags=["sql", "gold", "views", "definitions"],
    ),
]


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/notebooks", response_model=NotebookList, operation_id="listNotebooks")
async def list_notebooks(
    category: NotebookCategory | None = None,
) -> NotebookList:
    """
    List all Databricks notebooks in the payment analysis platform.
    
    Args:
        category: Optional filter by category
        
    Returns:
        List of notebooks with metadata
    """
    filtered = NOTEBOOKS
    
    if category:
        filtered = [n for n in filtered if n.category == category]
    
    # Count by category
    by_category = {}
    for notebook in NOTEBOOKS:
        cat = notebook.category.value
        by_category[cat] = by_category.get(cat, 0) + 1
    
    return NotebookList(
        notebooks=filtered,
        total=len(filtered),
        by_category=by_category,
    )


@router.get("/notebooks/{notebook_id}", response_model=NotebookInfo, operation_id="getNotebook")
async def get_notebook(notebook_id: str) -> NotebookInfo:
    """Get details for a specific notebook."""
    for notebook in NOTEBOOKS:
        if notebook.id == notebook_id:
            return notebook
    
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail=f"Notebook '{notebook_id}' not found")


@router.get("/notebooks/{notebook_id}/url", operation_id="getNotebookUrl")
async def get_notebook_url(notebook_id: str) -> dict[str, Any]:
    """
    Get the Databricks workspace URL for a notebook.
    
    Returns the full URL to open the notebook in Databricks.
    """
    notebook = await get_notebook(notebook_id)
    
    # Construct full Databricks URL
    # In production, get from environment or config
    base_url = "https://adb-984752964297111.11.azuredatabricks.net"
    
    # Replace workspace path template with actual username
    # This will be replaced dynamically in production
    workspace_path = notebook.workspace_path
    
    full_url = f"{base_url}/workspace{workspace_path}"
    
    return {
        "notebook_id": notebook_id,
        "name": notebook.name,
        "url": full_url,
        "workspace_path": workspace_path,
        "category": notebook.category.value,
    }


@router.get("/notebooks/categories/summary", operation_id="getNotebookCategorySummary")
async def get_category_summary() -> dict[str, Any]:
    """
    Get summary of notebooks by category with descriptions.
    
    Returns counts and notebook lists for each category.
    """
    summary = {}
    
    for category in NotebookCategory:
        notebooks_in_cat = [n for n in NOTEBOOKS if n.category == category]
        summary[category.value] = {
            "name": category.value.replace("_", " ").title(),
            "count": len(notebooks_in_cat),
            "notebooks": [
                {
                    "id": n.id,
                    "name": n.name,
                    "job_name": n.job_name,
                }
                for n in notebooks_in_cat
            ],
        }
    
    return {
        "categories": summary,
        "total_notebooks": len(NOTEBOOKS),
    }
