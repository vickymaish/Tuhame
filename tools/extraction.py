"""Conservative extraction of property facts from source text."""
import re
from datetime import datetime, timezone

from schemas import Contact, Contactability, ContactScope, ContactType, Evidence, EvidenceStatus, FinancialCharge, FinancialStatus, Freshness, FreshnessState, Listing, SearchCriteria, PricePeriod, PriceType, PropertyType, SourcePageStatus, SourceContentOrigin, TransactionType
from tools.contact_sources import is_general_agency_domain

_RENT = re.compile(r"(?:ksh|kes|kshs|price|rent)\s*[:.]?\s*([0-9][0-9,]*(?:\.\d+)?)\s*(?:/\s*month|per\s*month|monthly|pm)?", re.IGNORECASE)
_BEDS = re.compile(r"\b([1-9])\s*(?:-|\s)?(?:bed(?:room)?s?|br)\b", re.IGNORECASE)
_DATE = re.compile(r"\b(20\d{2})[-/](\d{1,2})[-/](\d{1,2})\b")
_LABELED_DATE = re.compile(r"\b(published|posted|available|updated|modified)\s*(?:on|:)?\s*(20\d{2})[-/](\d{1,2})[-/](\d{1,2})\b", re.IGNORECASE)
_AMENITIES = {"parking": "parking", "security": "security", "secure": "security", "furnished": "furnished", "balcony": "balcony", "pool": "pool", "gym": "gym"}
_CONTACT_PHONE = re.compile(r"(?:\+?254|0)\s?\d{3}\s?\d{3}\s?\d{3}\b")
_CONTACT_EMAIL = re.compile(r"\b[\w.+-]+@[\w.-]+\.\w{2,}\b")
_WHATSAPP_LINK = re.compile(r"https?://(?:api\.)?wa\.me/(?:\+|%2B)?(254\d{9}|0\d{9})[^\s\"'>]*", re.IGNORECASE)
_CHARGE_PATTERNS = {
    "parking": re.compile(r"parking\s*(?:fee|is|:)?\s*(?:ksh|kes)?\s*([0-9][0-9,]*)", re.IGNORECASE),
    "service_charge": re.compile(r"service\s+charge\s*(?:is|:)?\s*(?:ksh|kes)?\s*([0-9][0-9,]*)", re.IGNORECASE),
    "agency_fee": re.compile(r"agency\s+fee\s*(?:is|:)?\s*(?:ksh|kes)?\s*([0-9][0-9,]*)", re.IGNORECASE),
    "viewing_fee": re.compile(r"viewing\s+fee\s*(?:is|:)?\s*(?:ksh|kes)?\s*([0-9][0-9,]*)", re.IGNORECASE),
    "deposit": re.compile(r"deposit\s*(?:is|:)?\s*(?:ksh|kes)?\s*([0-9][0-9,]*)", re.IGNORECASE),
}


def _money(value: str) -> int:
    return int(float(value.replace(",", "")))


def _transaction_semantics(title: str, text: str, url: str | None) -> tuple[TransactionType, PricePeriod, PropertyType, str]:
    primary_text = re.split(r"\b(?:similar homes|similar listings|you may also like|similar properties)\b", text, maxsplit=1, flags=re.IGNORECASE)[0][:6000]
    source = f"{title} {url or ''} {primary_text}".lower()
    property_type = PropertyType.UNKNOWN
    if "apartment" in source or "flat" in source:
        property_type = PropertyType.APARTMENT
    elif "townhouse" in source:
        property_type = PropertyType.TOWNHOUSE
    elif "house" in source:
        property_type = PropertyType.HOUSE
    elif re.search(r"\bland\b|plot", source):
        property_type = PropertyType.LAND
    elif "commercial" in source or re.search(r"office|shop|warehouse|retail", source):
        property_type = PropertyType.COMMERCIAL

    if re.search(r"\b(?:land\s+for\s+sale|plot\s+(?:for\s+)?sale)\b", source):
        return TransactionType.LAND_SALE, PricePeriod.TOTAL, property_type, "land for sale"
    sale_signal = re.search(r"\b(?:for\s+sale|on\s+sale|property\s+sale)\b", source)
    rent_signal = re.search(r"\b(?:for\s+rent|to\s+let|rent:|per\s+month|monthly|/\s*mo(?:nth)?\b)\b", source)
    if sale_signal and not rent_signal:
        return TransactionType.SALE, PricePeriod.TOTAL, property_type, "for sale"
    if re.search(r"\bshort[- ]?let\b", source):
        period = PricePeriod.DAY if re.search(r"per\s+day|daily", source) else PricePeriod.MONTH
        return TransactionType.SHORT_LET, period, property_type, "short let"
    if re.search(r"\b(?:daily|per\s+day|nightly|per\s+night)\b", source):
        return TransactionType.RENT_DAILY, PricePeriod.DAY, property_type, "per day"
    if rent_signal or (property_type == PropertyType.APARTMENT and re.search(r"\b(?:rent|let)\b", source)):
        return (TransactionType.COMMERCIAL_RENT if property_type == PropertyType.COMMERCIAL else TransactionType.RENT_MONTHLY), PricePeriod.MONTH, property_type, "for rent/monthly"
    return TransactionType.UNKNOWN, PricePeriod.UNKNOWN, property_type, "transaction type not established"


def _rent_evidence(text: str, url: str | None, observed_at: datetime) -> tuple[int | None, list[Evidence], str | None]:
    text = re.split(r"\b(?:similar homes|similar listings|you may also like)\b", text, maxsplit=1, flags=re.IGNORECASE)[0]
    text = re.sub(r"price\s+range\s*:.*?(?=\b(?:rent|monthly|asking)\b|$)", " ", text, flags=re.IGNORECASE | re.DOTALL)
    excluded_context = r"(?:deposit|service\s+charge|parking\s+fee|agency\s+fee|viewing\s+fee|garbage|utility|internet)"
    matches = [
        match
        for match in _RENT.finditer(text)
        if not re.search(excluded_context + r"\s*$", text[max(0, match.start() - 32):match.start()], re.IGNORECASE)
        and not re.search(r"price\s+range", text[max(0, match.start() - 100):match.start()], re.IGNORECASE)
        and not (match.group(1).replace(",", "").split(".")[0].isdigit() and _money(match.group(1)) < 1000)
    ]
    evidence = []
    for match in matches:
        evidence.append(Evidence(claim="rent", value=_money(match.group(1)), evidence_text=match.group(0), source_url=url, observed_at=observed_at, status=EvidenceStatus.VERIFIED))

    range_match = re.search(r"(?:ksh|kes|kshs)?\s*[0-9][0-9,]*(?:\.\d+)?\s*(?:-|–|to)\s*(?:ksh|kes|kshs)?\s*[0-9][0-9,]*(?:\.\d+)?", text, re.IGNORECASE)
    if range_match and not matches:
        return None, [Evidence(claim="rent", evidence_text=range_match.group(0), source_url=url, observed_at=observed_at, status=EvidenceStatus.CONFLICT)], PriceType.PRICE_RANGE

    variant_match = re.search(r"(?:ksh|kes|kshs)?\s*[0-9][0-9,]*(?:\.\d+)?\s*(?:unfurnished|furnished)\s*/\s*(?:ksh|kes|kshs)?\s*[0-9][0-9,]*(?:\.\d+)?\s*(?:unfurnished|furnished)", text, re.IGNORECASE)
    if variant_match:
        variant_values = [_money(value) for value in re.findall(r"[0-9][0-9,]*(?:\.\d+)?", variant_match.group(0))]
        lower_variant = min(variant_values)
        return lower_variant, [Evidence(claim="rent", value=lower_variant, evidence_text=variant_match.group(0), source_url=url, observed_at=observed_at, status=EvidenceStatus.VERIFIED)], PriceType.VARIANT_PRICE

    table_variants = re.findall(r"(?:unfurnished|furnished)\s*\)?\s*\|\s*([0-9][0-9,]*(?:\.\d+)?)", text, re.IGNORECASE)
    if len(table_variants) >= 2:
        lower_variant = min(_money(value) for value in table_variants)
        return lower_variant, [Evidence(claim="rent", value=lower_variant, evidence_text="; ".join(table_variants), source_url=url, observed_at=observed_at, status=EvidenceStatus.VERIFIED)], PriceType.VARIANT_PRICE

    if re.search(r"\bfrom\b", text, re.IGNORECASE) and len(matches) == 1:
        return _money(matches[0].group(1)), evidence, PriceType.STARTING_FROM

    values = {_money(match.group(1)) for match in matches}
    explicit_price_mentions = re.findall(r"(?:price|rent|listed at|advertised|asking|ask)[^\d]{0,30}(?:ksh|kes|kshs)\s*([0-9][0-9,]*(?:\.\d+)?)", text, re.IGNORECASE)
    explicit_price_mentions.extend(re.findall(r"(?:main price|description says|listing says|stated)[^\d]{0,20}([0-9][0-9,]*(?:\.\d+)?)", text, re.IGNORECASE))
    explicit_values = {_money(value) for value in explicit_price_mentions}
    all_values = values | explicit_values
    if len(all_values) > 1:
        return None, [Evidence(claim="rent", evidence_text="; ".join(sorted(set(explicit_price_mentions))), source_url=url, observed_at=observed_at, status=EvidenceStatus.CONFLICT)], PriceType.CONFLICT
    if len(all_values) == 1:
        return next(iter(all_values)), evidence, PriceType.EXACT_PRICE
    if len(values) > 1:
        return None, [Evidence(claim="rent", evidence_text="; ".join(match.group(0) for match in matches), source_url=url, observed_at=observed_at, status=EvidenceStatus.CONFLICT)], PriceType.CONFLICT
    return None, [Evidence(claim="rent", source_url=url, observed_at=observed_at, status=EvidenceStatus.UNKNOWN)], None


def _freshness(text: str, url: str | None, observed_at: datetime) -> Freshness:
    labeled = []
    for match in _LABELED_DATE.finditer(text):
        label, year, month, day = match.groups()
        labeled.append((label.lower(), datetime(int(year), int(month), int(day), tzinfo=timezone.utc), match.group(0)))
    evidence = []
    published_at = next((date for label, date, _ in labeled if label in {"published", "posted"}), None)
    updated_at = next((date for label, date, _ in labeled if label in {"updated", "modified"}), None)
    availability_date = next((date for label, date, _ in labeled if label == "available"), None)
    for label, date, raw in labeled:
        evidence.append(Evidence(claim=f"{label}_at", value=date.isoformat(), evidence_text=raw, source_url=url, observed_at=observed_at, status=EvidenceStatus.VERIFIED))
    age_date = published_at or availability_date or updated_at
    if age_date:
        age_days = (observed_at - age_date).days
        state = FreshnessState.KNOWN_RECENT if age_days <= 30 else FreshnessState.KNOWN_OLD
        explanation = "Age is based on an explicit publication/availability/update date; freshness fields stay separate."
    else:
        state = FreshnessState.UNKNOWN
        explanation = "AGE UNKNOWN: no explicit publication or availability date was found."
    if not labeled and re.search(r"stale|old listing|no longer available", text, re.IGNORECASE):
        state = FreshnessState.STALE_SIGNAL
        explanation = "The source contains a stale or unavailable signal but no reliable publication date."
    return Freshness(state=state, published_at=published_at, updated_at=updated_at, availability_date=availability_date, evidence=evidence, explanation=explanation)


def _financial_charges(text: str, url: str | None, observed_at: datetime) -> list[FinancialCharge]:
    charges = []
    for name, pattern in _CHARGE_PATTERNS.items():
        included = re.search(rf"{name.replace('_', r'\s+')}\s+(?:is\s+)?included|included\s+(?:parking|service\s+charge)", text, re.IGNORECASE)
        if included:
            charges.append(FinancialCharge(name=name, status=FinancialStatus.INCLUDED, evidence=[Evidence(claim=name, value="included", evidence_text=included.group(0), source_url=url, observed_at=observed_at, status=EvidenceStatus.EXPLICIT)]))
            continue
        matches = list(pattern.finditer(text))
        if matches:
            amounts = {_money(match.group(1)) for match in matches}
            evidence = [Evidence(claim=name, value=_money(match.group(1)), evidence_text=match.group(0), source_url=url, observed_at=observed_at, status=EvidenceStatus.EXPLICIT) for match in matches]
            status = FinancialStatus.EXPLICIT_AMOUNT if len(amounts) == 1 else FinancialStatus.CONFLICT
            charges.append(FinancialCharge(name=name, amount=next(iter(amounts)) if len(amounts) == 1 else None, status=status, evidence=evidence))
    return charges


def _normalize_kenyan_phone(raw_value: str) -> str | None:
    digits = re.sub(r"\D", "", raw_value)
    if digits.startswith("0") and len(digits) == 10:
        return "+254" + digits[1:]
    if digits.startswith("254") and len(digits) == 12:
        return "+" + digits
    return None


def _contact_scope(context: str, url: str | None) -> ContactScope:
    lowered = context.lower()
    if re.search(r"property\s+(?:inquiries|enquiries)|listing\s+inquiries|call\s+about\s+this\s+property", lowered):
        return ContactScope.LISTING_SPECIFIC
    if re.search(r"\b(?:agent|call\s+[a-z][\w ]*)\b", lowered):
        return ContactScope.AGENT
    if re.search(r"property\s+manager|caretaker|manager", lowered):
        return ContactScope.PROPERTY_MANAGER
    if re.search(r"\b(?:office|general|our\s+(?:office|team)|agency)\b", lowered) or is_general_agency_domain(url):
        return ContactScope.AGENCY_GENERAL
    return ContactScope.UNKNOWN


def _contact_evidence(kind: ContactType, value: str | None, raw_value: str | None, source_url: str | None, evidence_text: str, observed_at: datetime, scope: ContactScope) -> Contact:
    normalized = _normalize_kenyan_phone(raw_value or "") if kind == ContactType.PHONE or kind == ContactType.WHATSAPP else None
    return Contact(kind=kind.value, type=kind, value=normalized or value, raw_value=raw_value, normalized_value=normalized, source_url=source_url, evidence=Evidence(claim=f"contact_{kind.value.lower()}", value=normalized or value, evidence_text=evidence_text, source_url=source_url, observed_at=observed_at, status=EvidenceStatus.EXPLICIT), contact_scope=scope)


def _contacts(text: str, url: str | None, observed_at: datetime) -> tuple[list[Contact], Contactability]:
    contacts = []
    whatsapp_number_pattern = re.compile(r"(?:whatsapp|wa)\s*(?:number|line|me)?\s*[:\-]?\s*((?:\+?254|0)\s?\d{3}\s?\d{3}\s?\d{3})", re.IGNORECASE)
    whatsapp_spans = [match.span(1) for match in whatsapp_number_pattern.finditer(text)]
    for match in _CONTACT_PHONE.finditer(text):
        if any(start <= match.start() < end for start, end in whatsapp_spans):
            continue
        start, end = match.span()
        sentence_start = max(text.rfind(".", 0, start), text.rfind("\n", 0, start)) + 1
        sentence_end = text.find(".", end)
        context = text[sentence_start:sentence_end if sentence_end != -1 else len(text)]
        contacts.append(_contact_evidence(ContactType.PHONE, None, match.group(0), url, context.strip(), observed_at, _contact_scope(context, url)))
    for match in whatsapp_number_pattern.finditer(text):
        contacts.append(_contact_evidence(ContactType.WHATSAPP, None, match.group(1), url, match.group(0), observed_at, _contact_scope(match.group(0), url)))
    for match in _WHATSAPP_LINK.finditer(text):
        contacts.append(_contact_evidence(ContactType.WHATSAPP, None, match.group(1), url, match.group(0), observed_at, _contact_scope("whatsapp " + match.group(0), url)))
    if re.search(r"(?:chat|contact|message)\s+(?:us|our team)?\s*on\s+whatsapp|whatsapp\s+(?:button|us)", text, re.IGNORECASE) and not any(contact.type == ContactType.WHATSAPP for contact in contacts):
        contacts.append(_contact_evidence(ContactType.WHATSAPP, None, None, url, re.search(r".{0,30}whatsapp.{0,40}", text, re.IGNORECASE).group(0), observed_at, ContactScope.UNKNOWN))
    for match in _CONTACT_EMAIL.finditer(text):
        start, end = match.span()
        context = text[max(0, start - 70):min(len(text), end + 70)]
        contacts.append(_contact_evidence(ContactType.EMAIL, match.group(0), match.group(0), url, context.strip(), observed_at, _contact_scope(context, url)))
    if re.search(r"<form\b|contact\s+(?:form|us)|send\s+an\s+inquiry", text, re.IGNORECASE):
        contacts.append(_contact_evidence(ContactType.CONTACT_FORM, None, None, url, "Public contact form", observed_at, ContactScope.LISTING_SPECIFIC))
    contacts = list({(contact.type, contact.value, contact.evidence.evidence_text): contact for contact in contacts}.values())
    if any(contact.type == ContactType.PHONE and contact.contact_scope in {ContactScope.LISTING_SPECIFIC, ContactScope.AGENT, ContactScope.PROPERTY_MANAGER} for contact in contacts):
        return contacts, Contactability.DIRECT_PHONE
    if any(contact.type == ContactType.WHATSAPP and contact.value for contact in contacts):
        return contacts, Contactability.WHATSAPP_WITH_NUMBER
    if any(contact.type == ContactType.WHATSAPP for contact in contacts):
        return contacts, Contactability.WHATSAPP_LINK_ONLY
    if any(contact.type == ContactType.EMAIL for contact in contacts):
        return contacts, Contactability.EMAIL
    if any(contact.type == ContactType.CONTACT_FORM for contact in contacts):
        return contacts, Contactability.CONTACT_FORM
    if any(contact.contact_scope == ContactScope.AGENCY_GENERAL for contact in contacts):
        return contacts, Contactability.AGENCY_CONTACT_ONLY
    return contacts, Contactability.NO_CONTACT if not contacts else Contactability.UNKNOWN


def _availability(text: str, url: str | None, observed_at: datetime) -> tuple[EvidenceStatus, list[Evidence]]:
    positive_patterns = [
        r"\bcurrently accepting inquiries\b",
        r"\bavailable for occupation\b",
        r"\bavailable\b",
        r"\bready for viewing\b",
    ]
    negative_patterns = [
        r"\bnot currently accepting inquiries\b",
        r"\bnot accepting inquiries\b",
        r"\bno longer accepting inquiries\b",
        r"\blisting is no longer available\b",
        r"\bno longer available\b",
        r"\bnot available\b",
        r"\bcurrently unavailable\b",
    ]

    sentences = re.split(r"(?<=[.!?])\s+|\n+", text.strip())
    positive = []
    negative = []
    evidence = []

    for sentence in sentences:
        sentence_negative = []
        sentence_positive = []
        for pattern in negative_patterns:
            for match in re.finditer(pattern, sentence, re.IGNORECASE):
                sentence_negative.append(match.group(0))
        for pattern in positive_patterns:
            for match in re.finditer(pattern, sentence, re.IGNORECASE):
                sentence_positive.append(match.group(0))

        if sentence_negative:
            negative.extend(sentence_negative)
            evidence.append(Evidence(claim="availability", value=False, evidence_text="; ".join(sorted(set(sentence_negative))), source_url=url, observed_at=observed_at, status=EvidenceStatus.EXPLICIT))
            continue

        if sentence_positive:
            positive.extend(sentence_positive)
            evidence.append(Evidence(claim="availability", value=True, evidence_text="; ".join(sorted(set(sentence_positive))), source_url=url, observed_at=observed_at, status=EvidenceStatus.EXPLICIT))

    if positive and negative:
        return EvidenceStatus.CONFLICT, evidence
    if negative:
        return EvidenceStatus.NOT_AVAILABLE, evidence
    if positive:
        return EvidenceStatus.AVAILABLE, evidence
    return EvidenceStatus.UNKNOWN, evidence


def extract_listing(title: str, text: str, source: str, url: str | None, criteria: SearchCriteria, observed_at: datetime | None = None) -> Listing:
    observed_at = observed_at or datetime.now(timezone.utc)
    source_text = f"{title}. {text}".strip()
    transaction_type, price_period, property_type, transaction_text = _transaction_semantics(title, text, url)
    extracted_price, evidence, price_type = _rent_evidence(source_text, url, observed_at)
    raw_price_strings = [item.evidence_text for item in evidence if item.claim == "rent" and item.evidence_text]
    sale_price = extracted_price if transaction_type in {TransactionType.SALE, TransactionType.LAND_SALE} else None
    rent = None if sale_price is not None else extracted_price
    if sale_price is not None:
        for item in evidence:
            if item.claim == "rent":
                item.claim = "sale_price"
    evidence.append(Evidence(claim="transaction_type", value=transaction_type.value, evidence_text=transaction_text, source_url=url, observed_at=observed_at, status=EvidenceStatus.EXPLICIT if transaction_type != TransactionType.UNKNOWN else EvidenceStatus.UNKNOWN))
    beds_match = _BEDS.search(source_text)
    beds = int(beds_match.group(1)) if beds_match else None
    if beds is not None:
        evidence.append(Evidence(claim="bedrooms", value=beds, evidence_text=beds_match.group(0), source_url=url, observed_at=observed_at, status=EvidenceStatus.VERIFIED))
    location = criteria.location if criteria.location.lower() in source_text.lower() else None
    if location:
        evidence.append(Evidence(claim="location", value=location, evidence_text=location, source_url=url, observed_at=observed_at, status=EvidenceStatus.VERIFIED))
    amenities = [label for phrase, label in _AMENITIES.items() if phrase in source_text.lower()]
    for amenity in sorted(set(amenities)):
        evidence.append(Evidence(claim=amenity, value=True, evidence_text=amenity, source_url=url, observed_at=observed_at, status=EvidenceStatus.VERIFIED))
    availability_status, availability_evidence = _availability(source_text, url, observed_at)
    evidence.extend(availability_evidence)
    # Round-trip default source state envelope without over-claiming.
    source_state = {
        "page_status": SourcePageStatus.CURRENT,
        "canonical_url": url,
        "source_checked_at": observed_at.isoformat(),
        "content_origin": SourceContentOrigin.LIVE_PAGE,
    }
    contacts, contactability = _contacts(source_text, url, observed_at)
    evidence.extend(contact.evidence for contact in contacts)
    listing = Listing(source=source, url=url, beds=beds, location=location, rent=rent, sale_price=sale_price, transaction_type=transaction_type, price_period=price_period, property_type=property_type, raw_price_strings=raw_price_strings, price_type=price_type or PriceType.EXACT_PRICE, amenities=sorted(set(amenities)), description=source_text, evidence=evidence, freshness=_freshness(source_text, url, observed_at), observed_at=observed_at, financial_charges=_financial_charges(source_text, url, observed_at), contacts=contacts, contactability=contactability, availability_status=availability_status, source_state=source_state)
    # keep compatibility for plain "rent"
    return listing
