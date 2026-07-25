from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


ArenaKind = Literal["capability", "security"]
InfraStatus = Literal["ok", "error", "skipped"]


@dataclass
class AgentSpec:
    tools: list[str] = field(default_factory=lambda: ["read_file", "write_file"])
    allow_paths: list[str] = field(default_factory=lambda: ["/workspace"])
    deny_paths: list[str] = field(
        default_factory=lambda: ["/hidden", "/secrets", "/arena", "/grade"]
    )
    mount: str = "/workspace"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AgentSpec:
        return cls(
            tools=list(data.get("tools") or ["read_file", "write_file"]),
            allow_paths=list(data.get("allow_paths") or ["/workspace"]),
            deny_paths=list(
                data.get("deny_paths") or ["/hidden", "/secrets", "/arena", "/grade"]
            ),
            mount=str(data.get("mount", "/workspace")),
        )


@dataclass
class GradingSpec:
    mode: str = "pristine_diff"
    hidden_root: str = "/hidden"
    command: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    universal_graders: list[dict[str, Any]] = field(
        default_factory=lambda: [{"type": "policy_violation"}]
    )
    graders: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GradingSpec:
        return cls(
            mode=str(data.get("mode", "pristine_diff")),
            hidden_root=str(data.get("hidden_root", "/hidden")),
            command=list(data.get("command") or []),
            env=dict(data.get("env") or {}),
            universal_graders=list(
                data.get("universal_graders") or [{"type": "policy_violation"}]
            ),
            graders=list(data.get("graders") or []),
        )


@dataclass
class ArenaSpec:
    id: str
    kind: ArenaKind
    prompt: str
    agent: AgentSpec = field(default_factory=AgentSpec)
    grading: GradingSpec = field(default_factory=GradingSpec)
    image: str = "python:3.12-slim"
    limits: dict[str, Any] = field(default_factory=dict)
    security_probes: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    root: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any], *, root: str = "") -> ArenaSpec:
        return cls(
            id=str(data["id"]),
            kind=data.get("kind", "capability"),  # type: ignore[arg-type]
            prompt=str(data.get("prompt", "")),
            agent=AgentSpec.from_dict(data.get("agent") or {}),
            grading=GradingSpec.from_dict(data.get("grading") or {}),
            image=str(data.get("image", "python:3.12-slim")),
            limits=dict(data.get("limits") or {}),
            security_probes=list(data.get("security_probes") or []),
            metadata=dict(data.get("metadata") or {}),
            root=root,
        )


@dataclass
class GradeResult:
    grader: str
    score: float
    passed: bool
    reasoning: str = ""
    infra_status: InfraStatus = "ok"
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PolicyEvent:
    kind: str
    detail: str
    severity: str = "medium"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ArenaRunResult:
    arena_id: str
    kind: ArenaKind
    passed: bool
    mean_score: float
    grades: list[GradeResult] = field(default_factory=list)
    policy_events: list[PolicyEvent] = field(default_factory=list)
    output: str | None = None
    transcript: list[dict[str, Any]] = field(default_factory=list)
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    infra_status: InfraStatus = "ok"
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "arena_id": self.arena_id,
            "kind": self.kind,
            "passed": self.passed,
            "mean_score": self.mean_score,
            "grades": [g.to_dict() for g in self.grades],
            "policy_events": [e.to_dict() for e in self.policy_events],
            "output": self.output,
            "transcript": self.transcript,
            "cost_usd": self.cost_usd,
            "latency_ms": self.latency_ms,
            "infra_status": self.infra_status,
            "error": self.error,
        }


@dataclass
class ModelCard:
    id: str
    provider: str = "mock"
    model: str | None = None
    tags: list[str] = field(default_factory=list)
    benchmarks: dict[str, float] = field(default_factory=dict)
    mock_script: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ModelCard:
        return cls(
            id=str(data["id"]),
            provider=str(data.get("provider", "mock")),
            model=data.get("model"),
            tags=list(data.get("tags") or []),
            benchmarks=dict(data.get("benchmarks") or {}),
            mock_script=list(data.get("mock_script") or []),
            metadata=dict(data.get("metadata") or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


SandboxMode = Literal["separate", "shared"]


@dataclass
class DebateParticipantResult:
    model_id: str
    passed: bool
    mean_score: float
    grades: list[GradeResult] = field(default_factory=list)
    policy_events: list[PolicyEvent] = field(default_factory=list)
    infra_status: InfraStatus = "ok"
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "passed": self.passed,
            "mean_score": self.mean_score,
            "grades": [g.to_dict() for g in self.grades],
            "policy_events": [e.to_dict() for e in self.policy_events],
            "infra_status": self.infra_status,
            "error": self.error,
        }


@dataclass
class DebateJudgeScore:
    model_id: str
    overall: float
    argumentation: float
    collaboration: float
    technical: float
    integrity: float
    reasoning: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DebateJudgeResult:
    winner: str | None
    scores: list[DebateJudgeScore] = field(default_factory=list)
    summary: str = ""
    judge_mode: str = "heuristic"
    judge_model: str | None = None
    infra_status: InfraStatus = "ok"
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "winner": self.winner,
            "scores": [s.to_dict() for s in self.scores],
            "summary": self.summary,
            "judge_mode": self.judge_mode,
            "judge_model": self.judge_model,
            "infra_status": self.infra_status,
            "error": self.error,
        }


@dataclass
class DebateResult:
    arena_id: str
    sandbox_mode: SandboxMode
    model_a_id: str
    model_b_id: str
    rounds: int
    timeline: list[dict[str, Any]] = field(default_factory=list)
    participants: list[DebateParticipantResult] = field(default_factory=list)
    shared_grade: DebateParticipantResult | None = None
    judge: DebateJudgeResult | None = None
    total_cost_usd: float = 0.0
    total_latency_ms: float = 0.0
    topic: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "arena_id": self.arena_id,
            "sandbox_mode": self.sandbox_mode,
            "model_a_id": self.model_a_id,
            "model_b_id": self.model_b_id,
            "rounds": self.rounds,
            "timeline": self.timeline,
            "participants": [p.to_dict() for p in self.participants],
            "shared_grade": self.shared_grade.to_dict() if self.shared_grade else None,
            "judge": self.judge.to_dict() if self.judge else None,
            "total_cost_usd": self.total_cost_usd,
            "total_latency_ms": self.total_latency_ms,
            "topic": self.topic,
        }


@dataclass
class Scorecard:
    model_id: str
    capability_score: float
    security_score: float
    capability_passed: bool
    security_passed: bool
    arenas: list[ArenaRunResult] = field(default_factory=list)
    by_domain: dict[str, float] = field(default_factory=dict)
    security_flags: list[str] = field(default_factory=list)
    total_cost_usd: float = 0.0
    total_latency_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "capability_score": self.capability_score,
            "security_score": self.security_score,
            "capability_passed": self.capability_passed,
            "security_passed": self.security_passed,
            "arenas": [a.to_dict() for a in self.arenas],
            "by_domain": self.by_domain,
            "security_flags": self.security_flags,
            "total_cost_usd": self.total_cost_usd,
            "total_latency_ms": self.total_latency_ms,
            "metadata": self.metadata,
        }
