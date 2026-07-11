"""auditar-sdk data models."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class DecisionRecord(BaseModel):
    decision_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    model_name: Optional[str] = None
    model_version: Optional[str] = None
    use_case: Optional[str] = None
    inputs: Optional[Dict[str, Any]] = None
    outputs: Optional[Dict[str, Any]] = None
    latency_ms: Optional[float] = None
    meta: Dict[str, Any] = Field(default_factory=dict)


class ModelRegistration(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    workspace: str
    model_name: str
    model_version: Optional[str] = None
    use_case: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class BatchRequest(BaseModel):
    batch_id: UUID = Field(default_factory=uuid4)
    decisions: List[DecisionRecord]
    created_at: datetime = Field(default_factory=datetime.utcnow)


class BatchResponse(BaseModel):
    batch_id: UUID
    accepted: int
    failed: int
    errors: List[str] = Field(default_factory=list)
