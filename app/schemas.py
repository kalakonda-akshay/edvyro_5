import json
import re
from datetime import date
from typing import Any, List, Literal, Optional, Union
from pydantic import BaseModel, ConfigDict, Field, field_validator

WorkMode = Literal["remote", "onsite", "hybrid"]
Status = Literal["open", "closed"]
UserRole = Literal["intern", "admin"]
SubmissionStatus = Literal["pending", "approved", "rejected"]

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
PHONE_REGEX = re.compile(r"^\+?[0-9\s\-()]{7,25}$")


class InternshipBase(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(min_length=3, max_length=120)
    company: str = Field(min_length=2, max_length=120)
    category: str = Field(default="Software Engineering", min_length=2, max_length=60)
    location: str = Field(min_length=1, max_length=120)
    work_mode: WorkMode
    duration: int = Field(default=3, ge=1, le=12)
    stipend: Optional[int] = Field(default=None, ge=0)
    skills: Union[str, List[str]] = Field(default_factory=list)
    description: str = Field(default="", max_length=5000)
    deadline: Optional[date] = None
    status: Status = "open"

    @field_validator("skills", mode="before")
    @classmethod
    def parse_skills(cls, v: Any) -> Union[str, List[str]]:
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                pass
        return v


class InternshipCreate(InternshipBase):
    pass


class InternshipReplace(InternshipBase):
    pass


class InternshipPatch(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: Optional[str] = Field(default=None, min_length=3, max_length=120)
    company: Optional[str] = Field(default=None, min_length=2, max_length=120)
    category: Optional[str] = Field(default=None, min_length=2, max_length=60)
    location: Optional[str] = Field(default=None, min_length=1, max_length=120)
    work_mode: Optional[WorkMode] = None
    duration: Optional[int] = Field(default=None, ge=1, le=12)
    stipend: Optional[int] = Field(default=None, ge=0)
    skills: Optional[Union[str, List[str]]] = None
    description: Optional[str] = Field(default=None, max_length=5000)
    deadline: Optional[date] = None
    status: Optional[Status] = None


class ApplicationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    full_name: str = Field(min_length=2, max_length=100, description="Full applicant name")
    email: str = Field(min_length=5, max_length=120, description="Contact email address")
    phone: str = Field(min_length=7, max_length=25, description="Contact telephone number")
    resume_url: str = Field(min_length=8, max_length=500, description="Public resume link (https://)")
    cover_letter: Optional[str] = Field(default="", max_length=2000, description="Cover statement")

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, value: str) -> str:
        clean = value.strip().lower()
        if not EMAIL_REGEX.match(clean):
            raise ValueError("Invalid email format (must be e.g. name@domain.com)")
        return clean

    @field_validator("phone")
    @classmethod
    def validate_phone_format(cls, value: str) -> str:
        clean = value.strip()
        if not PHONE_REGEX.match(clean):
            raise ValueError("Invalid phone number format (must contain 7-25 digits)")
        return clean

    @field_validator("resume_url")
    @classmethod
    def validate_resume_url(cls, value: str) -> str:
        clean = value.strip()
        if not (clean.startswith("http://") or clean.startswith("https://")):
            raise ValueError("Resume URL must begin with http:// or https://")
        return clean


class UserRegister(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=5, max_length=120)
    phone: str = Field(default="", max_length=25)
    college: str = Field(default="Engineering University", min_length=2, max_length=120)
    domain: str = Field(default="Full Stack Web Development", min_length=2, max_length=100)
    role: UserRole = "intern"

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, value: str) -> str:
        clean = value.strip().lower()
        if not EMAIL_REGEX.match(clean):
            raise ValueError("Invalid email format")
        return clean


class TaskSubmit(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    submission_url: str = Field(min_length=8, max_length=500, description="GitHub repository or live URL")
    notes: Optional[str] = Field(default="", max_length=2000, description="Deliverable notes and proof description")

    @field_validator("submission_url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        clean = value.strip()
        if not (clean.startswith("http://") or clean.startswith("https://")):
            raise ValueError("Submission URL must begin with http:// or https://")
        return clean


class TaskReview(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    status: SubmissionStatus
    feedback: Optional[str] = Field(default="", max_length=1000)


class CertificateIssue(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    user_id: int
    internship_title: Optional[str] = "Full Stack Engineering Internship"
    company: Optional[str] = "InternshipChesko Tech Labs"
    grade: Optional[str] = "Outstanding (A+)"
