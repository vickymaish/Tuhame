"""Controlled public contact-source metadata; no crawling is performed here."""

GENERAL_AGENCY_DOMAINS = {
    "oceanske.com",
    "amaliproperties.co.ke",
    "everroyalestates.co.ke",
    "omairarealtors.com",
    "azizirealtors.co.ke",
    "block.ke",
}

CONTROLLED_SOURCES = {
    "kenya_property_centre": {"homepage": "https://kenyapropertycentre.com/", "domain": "kenyapropertycentre.com", "default_scope": "UNKNOWN"},
    "kapsita": {"homepage": "https://kapsita.co.ke/", "domain": "kapsita.co.ke", "default_scope": "UNKNOWN"},
    "oceans_kenya": {"homepage": "https://www.oceanske.com/", "domain": "oceanske.com", "default_scope": "AGENCY_GENERAL"},
    "amali_properties": {"homepage": "https://amaliproperties.co.ke/", "domain": "amaliproperties.co.ke", "default_scope": "AGENCY_GENERAL"},
    "everroyal_estates": {"homepage": "https://www.everroyalestates.co.ke/", "domain": "everroyalestates.co.ke", "default_scope": "AGENCY_GENERAL"},
    "omaira_realtors": {"homepage": "https://www.omairarealtors.com/", "domain": "omairarealtors.com", "default_scope": "AGENCY_GENERAL"},
    "azizi_realtors": {"homepage": "https://azizirealtors.co.ke/", "domain": "azizirealtors.co.ke", "default_scope": "AGENCY_GENERAL"},
    "block_real_estate": {"homepage": "https://block.ke/", "domain": "block.ke", "default_scope": "AGENCY_GENERAL"},
}

CONTROLLED_SOURCE_DOMAINS = {
    "kenyapropertycentre.com",
    "kapsita.co.ke",
    *GENERAL_AGENCY_DOMAINS,
}


def source_domain(url: str | None) -> str:
    if not url:
        return ""
    return url.split("//", 1)[-1].split("/", 1)[0].lower().removeprefix("www.")


def is_general_agency_domain(url: str | None) -> bool:
    return source_domain(url) in GENERAL_AGENCY_DOMAINS