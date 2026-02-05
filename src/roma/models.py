"""ROMA result data models using Pydantic

Defines Pydantic models for ROMA (Reasoning-Oriented Modular Architecture)
result objects and WebSocket message structures for real-time visualization.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AtomizerResult(BaseModel):
    """Result from Atomizer module - determines if task is atomic

    The Atomizer analyzes whether a given task can be executed directly
    or needs to be decomposed into smaller subtasks.
    """

    is_atomic: bool = Field(
        ...,
        description="Whether the task is atomic (can execute directly) or needs decomposition"
    )

    node_type: str = Field(
        ...,
        description="Type of node: 'PLAN' for complex tasks or 'EXECUTE' for atomic tasks",
        pattern=r'^(PLAN|EXECUTE)$'
    )

    reasoning: str = Field(
        ...,
        description="Explanation of why this classification was made",
        min_length=1
    )

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when this atomization result was generated"
    )

    class Config:
        """Pydantic model configuration"""
        arbitrary_types_allowed = True
        use_enum_values = True
        validate_assignment = True
        json_schema_extra = {
            "example": {
                "is_atomic": False,
                "node_type": "PLAN",
                "reasoning": "This task requires multiple steps including research, analysis, and synthesis",
                "timestamp": "2026-02-03T12:00:00Z"
            }
        }

    def __str__(self) -> str:
        """String representation of the atomizer result"""
        return f"AtomizerResult(is_atomic={self.is_atomic}, node_type='{self.node_type}')"

    def __repr__(self) -> str:
        """Developer-friendly representation"""
        return (
            f"AtomizerResult(is_atomic={self.is_atomic}, node_type='{self.node_type}', "
            f"reasoning='{self.reasoning[:50]}...')"
        )


class SubTask(BaseModel):
    """Individual subtask from Planner module

    Represents a single step in a decomposed plan with dependencies.
    """

    id: str = Field(
        ...,
        description="Unique identifier for this subtask",
        min_length=1,
        pattern=r'^[a-zA-Z0-9_-]+$'
    )

    goal: str = Field(
        ...,
        description="Description of what this subtask should accomplish",
        min_length=1
    )

    dependencies: List[str] = Field(
        default_factory=list,
        description="List of subtask IDs that must complete before this one can start"
    )

    status: str = Field(
        default="pending",
        description="Current status of the subtask",
        pattern=r'^(pending|in_progress|completed|failed)$'
    )

    estimated_effort: Optional[int] = Field(
        default=None,
        description="Estimated effort in relative units (1-10)",
        ge=1,
        le=10
    )

    class Config:
        """Pydantic model configuration"""
        arbitrary_types_allowed = True
        use_enum_values = True
        validate_assignment = True
        json_schema_extra = {
            "example": {
                "id": "subtask_1",
                "goal": "Research the topic using available sources",
                "dependencies": [],
                "status": "pending",
                "estimated_effort": 3
            }
        }

    def __str__(self) -> str:
        """String representation of the subtask"""
        return f"SubTask(id='{self.id}', status='{self.status}')"

    def __repr__(self) -> str:
        """Developer-friendly representation"""
        return (
            f"SubTask(id='{self.id}', goal='{self.goal[:40]}...', "
            f"status='{self.status}', dependencies={self.dependencies})"
        )


class PlannerResult(BaseModel):
    """Result from Planner module - task decomposition

    The Planner breaks down complex tasks into executable subtasks
    and constructs a dependency graph for execution order.
    """

    subtasks: List[SubTask] = Field(
        ...,
        description="List of subtasks in the decomposed plan",
        min_length=1
    )

    dependencies_graph: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Graph mapping subtask IDs to their dependencies"
    )

    current_step: int = Field(
        default=0,
        description="Index of the current step in execution (0-based)",
        ge=0
    )

    total_estimated_effort: Optional[int] = Field(
        default=None,
        description="Total estimated effort for all subtasks",
        ge=0
    )

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when this plan was generated"
    )

    class Config:
        """Pydantic model configuration"""
        arbitrary_types_allowed = True
        use_enum_values = True
        validate_assignment = True
        json_schema_extra = {
            "example": {
                "subtasks": [
                    {
                        "id": "subtask_1",
                        "goal": "Research the topic",
                        "dependencies": [],
                        "status": "pending"
                    },
                    {
                        "id": "subtask_2",
                        "goal": "Synthesize findings",
                        "dependencies": ["subtask_1"],
                        "status": "pending"
                    }
                ],
                "dependencies_graph": {
                    "subtask_1": [],
                    "subtask_2": ["subtask_1"]
                },
                "current_step": 0,
                "timestamp": "2026-02-03T12:00:00Z"
            }
        }

    def __str__(self) -> str:
        """String representation of the planner result"""
        return f"PlannerResult(num_subtasks={len(self.subtasks)}, current_step={self.current_step})"

    def __repr__(self) -> str:
        """Developer-friendly representation"""
        return (
            f"PlannerResult(subtasks={len(self.subtasks)}, "
            f"current_step={self.current_step}/{len(self.subtasks)})"
        )


class ExecutorResult(BaseModel):
    """Result from Executor module - task execution

    The Executor performs the actual work of a task and returns
    the output along with supporting information.
    """

    output: str = Field(
        ...,
        description="The primary output or result of the execution",
        min_length=1
    )

    sources: List[str] = Field(
        default_factory=list,
        description="List of sources or references used in execution"
    )

    execution_time: float = Field(
        default=0.0,
        description="Time taken to execute this task in seconds",
        ge=0.0
    )

    token_usage: Optional[Dict[str, int]] = Field(
        default=None,
        description="Token usage statistics for LLM calls"
    )

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when this execution was completed"
    )

    class Config:
        """Pydantic model configuration"""
        arbitrary_types_allowed = True
        use_enum_values = True
        validate_assignment = True
        json_schema_extra = {
            "example": {
                "output": "The research findings indicate that...",
                "sources": ["source_1", "source_2"],
                "execution_time": 2.5,
                "timestamp": "2026-02-03T12:00:00Z"
            }
        }

    def __str__(self) -> str:
        """String representation of the executor result"""
        return f"ExecutorResult(output_length={len(self.output)}, execution_time={self.execution_time}s)"

    def __repr__(self) -> str:
        """Developer-friendly representation"""
        return (
            f"ExecutorResult(output='{self.output[:40]}...', "
            f"sources={len(self.sources)}, execution_time={self.execution_time}s)"
        )


class AggregatorResult(BaseModel):
    """Result from Aggregator module - synthesis of results

    The Aggregator combines results from multiple subtask executions
    into a coherent final result.
    """

    synthesized_result: str = Field(
        ...,
        description="The final synthesized result combining all component outputs",
        min_length=1
    )

    component_results: List[str] = Field(
        default_factory=list,
        description="List of individual results that were combined"
    )

    synthesis_method: str = Field(
        default="sequential",
        description="Method used for synthesis: 'sequential', 'hierarchical', 'parallel'",
        pattern=r'^(sequential|hierarchical|parallel)$'
    )

    confidence_score: Optional[float] = Field(
        default=None,
        description="Confidence in the synthesized result (0.0 to 1.0)",
        ge=0.0,
        le=1.0
    )

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when this aggregation was performed"
    )

    class Config:
        """Pydantic model configuration"""
        arbitrary_types_allowed = True
        use_enum_values = True
        validate_assignment = True
        json_schema_extra = {
            "example": {
                "synthesized_result": "Combining all findings, we conclude that...",
                "component_results": ["Result from subtask 1", "Result from subtask 2"],
                "synthesis_method": "sequential",
                "confidence_score": 0.85,
                "timestamp": "2026-02-03T12:00:00Z"
            }
        }

    def __str__(self) -> str:
        """String representation of the aggregator result"""
        return f"AggregatorResult(components={len(self.component_results)}, method='{self.synthesis_method}')"

    def __repr__(self) -> str:
        """Developer-friendly representation"""
        return (
            f"AggregatorResult(result='{self.synthesized_result[:40]}...', "
            f"components={len(self.component_results)}, confidence={self.confidence_score})"
        )


class VerifierResult(BaseModel):
    """Result from Verifier module - output validation

    The Verifier checks the quality and correctness of results
    before they are returned to the user.
    """

    verdict: bool = Field(
        ...,
        description="Whether the result passed verification (True) or failed (False)"
    )

    feedback: str = Field(
        ...,
        description="Detailed feedback explaining the verdict",
        min_length=1
    )

    quality_score: float = Field(
        default=0.0,
        description="Quality score assigned to the result (0.0 to 1.0)",
        ge=0.0,
        le=1.0
    )

    issues_found: List[str] = Field(
        default_factory=list,
        description="List of specific issues identified during verification"
    )

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when this verification was performed"
    )

    class Config:
        """Pydantic model configuration"""
        arbitrary_types_allowed = True
        use_enum_values = True
        validate_assignment = True
        json_schema_extra = {
            "example": {
                "verdict": True,
                "feedback": "The result is comprehensive and well-supported",
                "quality_score": 0.9,
                "issues_found": [],
                "timestamp": "2026-02-03T12:00:00Z"
            }
        }

    def __str__(self) -> str:
        """String representation of the verifier result"""
        status = "PASSED" if self.verdict else "FAILED"
        return f"VerifierResult(verdict={status}, quality={self.quality_score})"

    def __repr__(self) -> str:
        """Developer-friendly representation"""
        return (
            f"VerifierResult(verdict={self.verdict}, quality={self.quality_score}, "
            f"feedback='{self.feedback[:40]}...')"
        )


class WebSocketMessage(BaseModel):
    """Base WebSocket message structure

    Defines the standard format for all messages sent over the WebSocket
    connection between the ROMA backend and the visualization frontend.
    """

    type: str = Field(
        ...,
        description="Message type: 'atomizer', 'planner', 'executor', 'aggregator', 'verifier', 'error', 'complete'",
        pattern=r'^(atomizer|planner|executor|aggregator|verifier|error|complete|status)$'
    )

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when this message was sent"
    )

    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Message payload containing the actual data"
    )

    message_id: Optional[str] = Field(
        default=None,
        description="Unique identifier for this message (useful for tracking)"
    )

    session_id: Optional[str] = Field(
        default=None,
        description="Session identifier for grouping related messages"
    )

    class Config:
        """Pydantic model configuration"""
        arbitrary_types_allowed = True
        use_enum_values = True
        validate_assignment = True
        json_schema_extra = {
            "example": {
                "type": "atomizer",
                "timestamp": "2026-02-03T12:00:00Z",
                "data": {
                    "is_atomic": False,
                    "node_type": "PLAN",
                    "reasoning": "Task requires decomposition"
                },
                "message_id": "msg_123",
                "session_id": "session_456"
            }
        }

    def __str__(self) -> str:
        """String representation of the WebSocket message"""
        return f"WebSocketMessage(type='{self.type}', message_id='{self.message_id}')"

    def __repr__(self) -> str:
        """Developer-friendly representation"""
        return (
            f"WebSocketMessage(type='{self.type}', "
            f"data_keys={list(self.data.keys())}, timestamp='{self.timestamp}')"
        )


class ReasoningUpdate(WebSocketMessage):
    """Real-time reasoning update for streaming

    Extends the base WebSocket message with additional fields
    specifically for reasoning visualization.
    """

    module: str = Field(
        ...,
        description="Which ROMA module produced this update: 'atomizer', 'planner', 'executor', 'aggregator', 'verifier'",
        pattern=r'^(atomizer|planner|executor|aggregator|verifier)$'
    )

    stage: str = Field(
        ...,
        description="Processing stage: 'input', 'processing', 'output', 'error'",
        pattern=r'^(input|processing|output|error)$'
    )

    content: str = Field(
        ...,
        description="Human-readable content for display in the visualization",
        min_length=1
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata for the visualization component"
    )

    class Config:
        """Pydantic model configuration"""
        arbitrary_types_allowed = True
        use_enum_values = True
        validate_assignment = True
        json_schema_extra = {
            "example": {
                "type": "atomizer",
                "module": "atomizer",
                "stage": "processing",
                "content": "Analyzing task complexity...",
                "timestamp": "2026-02-03T12:00:00Z",
                "data": {
                    "is_atomic": False,
                    "node_type": "PLAN"
                },
                "metadata": {
                    "confidence": 0.95
                }
            }
        }

    def __str__(self) -> str:
        """String representation of the reasoning update"""
        return f"ReasoningUpdate(module='{self.module}', stage='{self.stage}')"

    def __repr__(self) -> str:
        """Developer-friendly representation"""
        return (
            f"ReasoningUpdate(module='{self.module}', stage='{self.stage}', "
            f"content='{self.content[:40]}...')"
        )
