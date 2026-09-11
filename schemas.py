"""Shared Nyumba Hunter schemas."""
from datetime import date, datetime
from enum import Enum, StrEnum
from typing import Any

from pydantic import BaseModel, Field


class EvidenceStatus(StrEnum):
    VERIFIED = "VERIFIED"
    EXPLICIT = "EXPLICIT"
    UNKNOWN = "UNKNOWN"
    NOT_MENTIONED = "NOT_MENTIONED"
    CONFLICT = "CONFLICT"
    UNVERIFIED = "UNVERIFIED"
    STALE_SIGNAL = "STALE_SIGNAL"
    AVAILABLE = "AVAILABLE"
    NOT_AVAILABLE = "NOT_AVAILABLE"


class ContactType(StrEnum):
    PHONE = "PHONE"
    WHATSAPP = "WHATSAPP"
    EMAIL = "EMAIL"
    CONTACT_FORM = "CONTACT_FORM"


class ContactScope(StrEnum):
    LISTING_SPECIFIC = "LISTING_SPECIFIC"
    AGENT = "AGENT"
    PROPERTY_MANAGER = "PROPERTY_MANAGER"
    AGENCY_GENERAL = "AGENCY_GENERAL"
    UNKNOWN = "UNKNOWN"


class Contactability(StrEnum):
    DIRECT_PHONE = "DIRECT_PHONE"
    WHATSAPP_WITH_NUMBER = "WHATSAPP_WITH_NUMBER"
    WHATSAPP_LINK_ONLY = "WHATSAPP_LINK_ONLY"
    EMAIL = "EMAIL"
    CONTACT_FORM = "CONTACT_FORM"
    AGENCY_CONTACT_ONLY = "AGENCY_CONTACT_ONLY"
    NO_CONTACT = "NO_CONTACT"
    UNKNOWN = "UNKNOWN"


class PriceType(StrEnum):
    EXACT_PRICE = "EXACT_PRICE"
    STARTING_FROM = "STARTING_FROM"
    PRICE_RANGE = "PRICE_RANGE"
    VARIANT_PRICE = "VARIANT_PRICE"
    CONFLICT = "CONFLICT"


class TransactionType(StrEnum):
    RENT_MONTHLY = "RENT_MONTHLY"
    RENT_DAILY = "RENT_DAILY"
    SHORT_LET = "SHORT_LET"
    SALE = "SALE"
    LAND_SALE = "LAND_SALE"
    COMMERCIAL_RENT = "COMMERCIAL_RENT"
    UNKNOWN = "UNKNOWN"


class PricePeriod(StrEnum):
    MONTH = "MONTH"
    DAY = "DAY"
    TOTAL = "TOTAL"
    UNKNOWN = "UNKNOWN"


class PropertyType(StrEnum):
    APARTMENT = "APARTMENT"
    HOUSE = "HOUSE"
    TOWNHOUSE = "TOWNHOUSE"
    LAND = "LAND"
    COMMERCIAL = "COMMERCIAL"
    UNKNOWN = "UNKNOWN"


class SourcePageStatus(StrEnum):
    CURRENT = "CURRENT"
    EXPIRED = "EXPIRED"
    REDIRECTED = "REDIRECTED"
    ERROR = "ERROR"


class SourceContentOrigin(StrEnum):
    LIVE_PAGE = "LIVE_PAGE"
    SEARCH_INDEX = "SEARCH_INDEX"
    CACHE = "CACHE"


class FinancialStatus(StrEnum):
    INCLUDED = "INCLUDED"
    EXPLICIT_AMOUNT = "EXPLICIT_AMOUNT"
    UNKNOWN = "UNKNOWN"
    NOT_MENTIONED = "NOT_MENTIONED"
    CONFLICT = "CONFLICT"


class FreshnessState(StrEnum):
    KNOWN_RECENT = "KNOWN_RECENT"
    KNOWN_OLD = "KNOWN_OLD"
    STALE_SIGNAL = "STALE_SIGNAL"
    UNKNOWN = "UNKNOWN"


class Evidence(BaseModel):
    claim: str
    value: str | int | float | None = None
    evidence_text: str | None = None
    source_url: str | None = None
    observed_at: datetime
    status: EvidenceStatus = EvidenceStatus.UNKNOWN


class Freshness(BaseModel):
    state: FreshnessState = FreshnessState.UNKNOWN
    published_at: datetime | None = None
    updated_at: datetime | None = None
    availability_date: datetime | None = None
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None
    evidence: list[Evidence] = Field(default_factory=list)
    explanation: str


class FinancialCharge(BaseModel):
    name: str
    amount: int | None = None
    status: FinancialStatus
    evidence: list[Evidence] = Field(default_factory=list)


class Contact(BaseModel):
    kind: str
    type: ContactType | None = None
    value: str | None = None
    raw_value: str | None = None
    normalized_value: str | None = None
    source_url: str | None = None
    evidence: Evidence
    contact_scope: ContactScope = ContactScope.UNKNOWN
    confidence_state: EvidenceStatus = EvidenceStatus.EXPLICIT


class SearchCriteria(BaseModel):
    beds: int | None = Field(default=None, ge=1, le=10)
    location: str
    location_raw: str | None = None
    locations: list[str] = Field(default_factory=list)
    max_rent: int | None = Field(default=None, gt=0)
    transaction_type: TransactionType = TransactionType.RENT_MONTHLY
    must_haves: list[str] = []
    negotiables: list[str] = []
    move_timeline: str | None = None


class Listing(BaseModel):
    source: str
    url: str | None = None
    beds: int | None = None
    location: str | None = None
    rent: int | None = None
    sale_price: int | None = None
    transaction_type: TransactionType = TransactionType.UNKNOWN
    price_period: PricePeriod = PricePeriod.UNKNOWN
    property_type: PropertyType = PropertyType.UNKNOWN
    raw_price_strings: list[str] = Field(default_factory=list)
    price_type: PriceType | None = None
    price_text: str | None = None
    deposit: int | None = None
    service_charge: int | None = None
    parking_fee: int | None = None
    agency_fee: int | None = None
    viewing_fee: int | None = None
    booking_fee: int | None = None
    garbage_fee: int | None = None
    utilities: int | None = None
    internet: int | None = None
    other_mandatory_charges: int | None = None
    amenities: list[str] = Field(default_factory=list)
    description: str
    agent_contact: str | None = None
    posted_days: int | None = None
    evidence: list[Evidence] = Field(default_factory=list)
    freshness: Freshness
    observed_at: datetime
    observation_history: dict = Field(default_factory=dict)
    image_urls: list[str] = Field(default_factory=list)
    financial_charges: list[FinancialCharge] = Field(default_factory=list)
    contacts: list[Contact] = Field(default_factory=list)
    contactability: Contactability = Contactability.NO_CONTACT
    availability_status: EvidenceStatus = EvidenceStatus.UNKNOWN
    source_state: dict = Field(default_factory=lambda: {
        "page_status": SourcePageStatus.CURRENT,
        "canonical_url": None,
        "source_checked_at": None,
        "content_origin": SourceContentOrigin.LIVE_PAGE,
    })


class VerificationDecision(BaseModel):
    status: EvidenceStatus
    flags: list[str] = Field(default_factory=list)
    required_actions: list[str] = Field(default_factory=list)


class Survivor(BaseModel):
    listing: Listing
    match_reasons: list[str] = Field(default_factory=list)
    comp_stats: dict = Field(default_factory=dict)
    red_flags: list[str] = Field(default_factory=list)
    negotiation_log: list[dict] = Field(default_factory=list)
    final_terms: dict | None = None
    viewing_slot: str | None = None
    status: str = "shortlisted"
    verification: VerificationDecision | None = None


class PipelineResult(BaseModel):
    criteria: SearchCriteria
    discovered: int
    duplicates_removed: int
    rejected: list[dict] = Field(default_factory=list)
    survivors: list[Survivor] = Field(default_factory=list)
    duplicate_conflicts: list[dict] = Field(default_factory=list)
    events: list[dict] = Field(default_factory=list)


def to_jsonable(value: Any) -> Any:
    """Return a nested object graph safe for json.dumps without losing date timestamps."""
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_jsonable(item) for item in value]
    return value
