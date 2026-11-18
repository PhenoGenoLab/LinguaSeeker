"""Typed contracts for the source-grounded fact chain.

The chain is the product cutover of the approved research route
``npj_native_v3.source_fact_chain``:

    source windows -> source fact extraction -> source verification
    -> fact-level English presentation -> bilingual rows

There is exactly one fact set per run. ``SourceFact`` records are the only
facts; verifications and English views reference them by ``fact_id`` and
never create, delete or rewrite a source fact.
"""

from __future__ import annotations

from enum import Enum
import hashlib
import json

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Polarity(str, Enum):
    """Author-stated polarity of a fact."""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    UNCERTAIN = "uncertain"


class SubjectStatus(str, Enum):
    """Whether the fact is attributed to an identifiable subject."""

    KNOWN = "known"
    UNKNOWN = "unknown"


class VerificationLabel(str, Enum):
    """Source-window verification outcome for one candidate fact."""

    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    UNCERTAIN = "uncertain"
    UNVERIFIED = "unverified"


class EnglishStatus(str, Enum):
    """How an English presentation view was produced."""

    TRANSLATED = "translated"
    PASSTHROUGH = "passthrough"
    PRESERVED = "preserved"
    FAILED = "failed"
    MISSING = "missing"


class PresentationMode(str, Enum):
    """Whether a field is kept verbatim or translated for presentation."""

    PRESERVED = "preserved"
    PRESENTED = "presented"


class StageName(str, Enum):
    EXTRACT = "extract"
    VERIFY = "verify"
    TRANSLATE = "translate"


class StageOutcome(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    EMPTY = "empty"


STAGE_NAMES: tuple[StageName, ...] = (StageName.EXTRACT, StageName.VERIFY, StageName.TRANSLATE)

# Product catalog ids are used so the resulting facts feed Phase 4
# standardization without an id translation layer. Gene, variant and age
# strings are preserved verbatim; phenotype and inheritance are translated.
FIELD_MODES: dict[str, PresentationMode] = {
    "A.gene_symbol": PresentationMode.PRESERVED,
    "A.variant_hgvs_c": PresentationMode.PRESERVED,
    "A.variant_hgvs_p": PresentationMode.PRESERVED,
    "B.age_of_onset": PresentationMode.PRESERVED,
    "B.clinical_phenotypes": PresentationMode.PRESENTED,
    "B.mode_of_inheritance_reported": PresentationMode.PRESENTED,
}
ALLOWED_FIELD_IDS: tuple[str, ...] = tuple(FIELD_MODES)
POLARITIES: frozenset[str] = frozenset(item.value for item in Polarity)
VERIFY_LABELS: frozenset[str] = frozenset(
    {VerificationLabel.SUPPORTED.value, VerificationLabel.UNSUPPORTED.value, VerificationLabel.UNCERTAIN.value}
)
# Only supported facts are promoted into clinical evidence (Phase 4).
EVIDENCE_LABELS: frozenset[str] = frozenset({VerificationLabel.SUPPORTED.value})


class ChainContractError(ValueError):
    """A candidate fact or provider reply breaks a named contract."""

    def __init__(self, reason: str, detail: str = "") -> None:
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason


class SourceHashMismatch(Exception):
    """Source bytes do not match the recorded hash; raised before any provider call."""


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_json(obj: object) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


class Subject(BaseModel):
    """Subject attribution. ``unknown`` never receives an identifier."""

    model_config = ConfigDict(frozen=True)

    status: SubjectStatus
    subject_id: str | None = None

    @model_validator(mode="after")
    def validate_subject(self) -> Subject:
        if self.status == SubjectStatus.KNOWN and not self.subject_id:
            raise ValueError("subject_known_without_id")
        if self.status == SubjectStatus.UNKNOWN and self.subject_id is not None:
            raise ValueError("subject_unknown_with_id")
        return self


class SourceDocument(BaseModel):
    """Frozen source text bound to its SHA-256. Every stage sees only this text."""

    model_config = ConfigDict(frozen=True)

    document_id: str
    text: str
    language: str
    source_hash: str


class DocumentWindow(BaseModel):
    """A bounded, non-silent chunk of the source document."""

    model_config = ConfigDict(frozen=True)

    window_id: int
    text: str
    start_offset: int
    end_offset: int

    @property
    def length(self) -> int:
        return self.end_offset - self.start_offset

    @property
    def label(self) -> str:
        return f"w{self.window_id:04d}"


class WindowPlanEntry(BaseModel):
    document_id: str
    window_id: str
    start: int
    end: int


class SourceFact(BaseModel):
    """One immutable source fact with its verbatim quote and document span."""

    model_config = ConfigDict(frozen=True)

    fact_id: str
    document_id: str
    source_hash: str
    field_id: str
    raw_value: str
    polarity: Polarity
    subject: Subject
    quote: str
    span_start: int
    span_end: int
    window_id: str

    @property
    def span(self) -> tuple[int, int]:
        return self.span_start, self.span_end


class Verification(BaseModel):
    """Source-grounded label for a fact; never rewrites the fact."""

    model_config = ConfigDict(frozen=True)

    fact_id: str
    label: VerificationLabel
    reason: str
    model_id: str | None = None
    prompt_version: str | None = None


class EnglishView(BaseModel):
    """English representation linked to a source fact.

    Polarity and subject are copied from the fact, never taken from the
    translation reply. Only the presented text is produced in English.
    """

    model_config = ConfigDict(frozen=True)

    fact_id: str
    field_id: str
    mode: PresentationMode
    status: EnglishStatus
    english_text: str | None
    polarity: Polarity
    subject: Subject
    presentation_version: str | None
    model_id: str | None = None
    error: str | None = None


class BilingualRow(BaseModel):
    """One display row: source fact + verification + its English views."""

    fact: SourceFact
    verification: Verification | None = None
    english: list[EnglishView] = Field(default_factory=list)


class StageProgress(BaseModel):
    """Per-window, per-stage progress retained for audit and resumability."""

    document_id: str
    window_id: str
    start: int
    end: int
    stage: StageName
    outcome: StageOutcome | None = None
    detail: str = ""


class ChainEvent(BaseModel):
    """Append-only audit event for one chain run."""

    stage: StageName
    event: str
    window_id: str | None = None
    fact_id: str | None = None
    detail: str | None = None


class Rejection(BaseModel):
    """A candidate or reply item refused by a named contract."""

    stage: StageName
    window_id: str | None = None
    reason: str
    detail: str = ""


class ChainConfig(BaseModel):
    """Model ids and windowing parameters for one run."""

    extract_model: str
    verify_model: str
    translate_model: str
    window_chars: int = 4000
    window_overlap: int = 200
    max_attempts: int = 2
    # 0 disables the hard call cap; positive values abort the run when reached.
    max_provider_calls: int = 0
    allowed_field_ids: tuple[str, ...] = ALLOWED_FIELD_IDS

    @model_validator(mode="after")
    def validate_window(self) -> ChainConfig:
        if self.window_chars <= 0:
            raise ValueError("window_chars must be positive")
        if self.window_overlap < 0 or self.window_overlap >= self.window_chars:
            raise ValueError("window_overlap must be >= 0 and < window_chars")
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        unknown = [field for field in self.allowed_field_ids if field not in FIELD_MODES]
        if unknown:
            raise ValueError(f"unknown extraction field ids: {unknown}")
        return self


class PromptVersions(BaseModel):
    """Prompt and presentation identities that produced one chain run."""

    model_config = ConfigDict(frozen=True)

    extract: str
    verify: str
    translate: str
    presentation: str


class ChainRun(BaseModel):
    """Complete, typed result of one chain execution over one document."""

    document_id: str
    source_hash: str
    language: str
    config: ChainConfig
    # ``None`` means the run predates version tracking and must be rebuilt.
    prompt_versions: PromptVersions | None = None
    windows: list[WindowPlanEntry] = Field(default_factory=list)
    facts: list[SourceFact] = Field(default_factory=list)
    verifications: list[Verification] = Field(default_factory=list)
    english: list[EnglishView] = Field(default_factory=list)
    stage_progress: list[StageProgress] = Field(default_factory=list)
    events: list[ChainEvent] = Field(default_factory=list)
    rejections: list[Rejection] = Field(default_factory=list)
    provider_calls: int = 0

    def verification_for(self, fact_id: str) -> Verification | None:
        for verification in self.verifications:
            if verification.fact_id == fact_id:
                return verification
        return None

    def english_for(self, fact_id: str) -> list[EnglishView]:
        return [view for view in self.english if view.fact_id == fact_id]

    def bilingual_rows(self) -> list[BilingualRow]:
        """Join facts, labels and English views by fact_id, adding no facts."""
        return [
            BilingualRow(
                fact=fact,
                verification=self.verification_for(fact.fact_id),
                english=self.english_for(fact.fact_id),
            )
            for fact in self.facts
        ]

    def event(self, stage: StageName, event: str, **kwargs: object) -> None:
        self.events.append(ChainEvent(stage=stage, event=event, **kwargs))  # type: ignore[arg-type]
