from datetime import date, datetime, timezone
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

Kind = Literal["projects", "milestones", "tickets", "roles", "documents", "runs"]
DocumentType = Literal[
    "unclassified", "product-vision", "user-story", "architecture-topic",
    "design-topic", "design-canvas", "screen-inventory", "review-report", "review-evidence",
]
WorkType = Literal["UNCLASSIFIED", "BUILD", "BUG"]
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=240)]
Text = Annotated[str, StringConstraints(max_length=100_000)]


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    name: Name


class Project(Record):
    description: Text = ""
    checkout_path: Annotated[str, StringConstraints(strip_whitespace=True, max_length=4096)] = ""


class Milestone(Record):
    description: Text = ""
    project: Name


class Role(Milestone):
    instructions: Text = ""


TagId = Annotated[str, StringConstraints(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$", max_length=120)]

class TaggedRecord(Record):
    tags: list[TagId] = Field(default_factory=list, max_length=200)

    @field_validator("tags")
    @classmethod
    def unique_tags(cls, values):
        if len(values) != len(set(values)):
            raise ValueError("Use each tag once.")
        return values


class Document(TaggedRecord):
    project: Name
    document_type: DocumentType = "unclassified"
    description: Text = ""
    content: Annotated[str, StringConstraints(min_length=1, max_length=100_000)]
    source_documents: list[Name] = Field(default_factory=list, max_length=200, description="Source documents this document depends on, in the same project.")

    @field_validator("content")
    @classmethod
    def nonblank_content(cls, value):
        if not value.strip():
            raise ValueError("Document content must contain text.")
        return value

    @field_validator("source_documents")
    @classmethod
    def unique_sources(cls, values):
        if len(values) != len(set(values)):
            raise ValueError("List each source document once.")
        return values


CriterionId = Annotated[str, StringConstraints(pattern=r"^[a-z0-9][a-z0-9_-]{0,79}$")]
ProofStatus = Literal["unverified", "verified", "superseded"]
PreviewDigest = Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]


class CriterionTarget(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    document_id: Name


class CriterionDesign(CriterionTarget):
    version: int = Field(gt=0)


class ReportProof(CriterionTarget):
    kind: Literal["report"]
    revision: int = Field(gt=0)
    section_line: int | None = Field(default=None, ge=0)
    status: ProofStatus = "unverified"


class ScreenshotProof(CriterionTarget):
    kind: Literal["screenshot"]
    filename: Annotated[str, StringConstraints(min_length=1, max_length=124)]
    digest: PreviewDigest
    status: ProofStatus = "unverified"


CriterionProof = Annotated[ReportProof | ScreenshotProof, Field(discriminator="kind")]


class TicketCriterion(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    id: CriterionId
    text: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=4000)]
    evidence_required: bool = False
    design: CriterionDesign | None = None
    evidence: list[CriterionProof] = Field(default_factory=list, max_length=20)

    @field_validator("evidence")
    @classmethod
    def unique_targets(cls, values):
        targets = [tuple(proof.model_dump(exclude={"status"}).items()) for proof in values]
        if len(targets) != len(set(targets)):
            raise ValueError("List each exact evidence target once per criterion.")
        return values


class Ticket(Milestone, TaggedRecord):
    milestone: Name
    status: Literal["Planned", "In progress", "Blocked", "Done"] = "Planned"
    role: str = ""
    due: str = ""
    work_type: WorkType = "UNCLASSIFIED"
    execution_role: Literal["", "FE", "BE"] = ""
    documents: list[Name] = Field(default_factory=list, max_length=200, description="Context document IDs used as inputs.")
    output_documents: list[Name] = Field(default_factory=list, max_length=200, description="Output document IDs produced by the work.")
    criteria: list[TicketCriterion] = Field(default_factory=list, max_length=60, description="Stable acceptance criteria with optional pinned design and evidence references.")

    @field_validator("due")
    @classmethod
    def calendar_date(cls, value):
        if value and date.fromisoformat(value).isoformat() != value:
            raise ValueError("Use YYYY-MM-DD.")
        return value

    @field_validator("documents", "output_documents")
    @classmethod
    def unique_documents(cls, values):
        if len(values) != len(set(values)):
            raise ValueError("Each document may be linked once per relationship.")
        return values

    @field_validator("criteria")
    @classmethod
    def unique_criteria(cls, values):
        if len(values) != len({criterion.id for criterion in values}):
            raise ValueError("Use a distinct ID for each acceptance criterion.")
        return values


class Run(Record):
    project: Name
    ticket: str = ""
    agent: Literal["Codex", "Claude", "InApp Assistant"]
    status: Literal["Queued", "Running", "Waiting for input", "Blocked", "Completed", "Failed", "Cancelled"]
    note: Text = ""
    mode: Literal["Edit", "Read only"] = "Edit"


def timestamp():
    return datetime.now(timezone.utc).isoformat()


MODELS = dict(projects=Project, milestones=Milestone, tickets=Ticket, roles=Role, documents=Document, runs=Run)
PREFIX = dict(projects="P", milestones="M", tickets="AB", roles="R", documents="D", runs="RUN")
