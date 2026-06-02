import enum


class UserRole(str, enum.Enum):
    admin = "admin"
    member = "member"


class SignupRequestStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class DocumentStatus(str, enum.Enum):
    draft = "draft"
    published = "published"


class ReactionType(str, enum.Enum):
    like = "like"
