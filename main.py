"""Tuhame command-line investigation demo."""
import json
import re
import sys

from agent_loop import run
from report import write_report
from schemas import SearchCriteria, TransactionType, to_jsonable


def parse_request(request: str) -> SearchCriteria:
    beds_match = re.search(r"(\d+)\s*[- ]?bed", request, re.IGNORECASE)
    rent_match = re.search(r"(?:max|maximum|under|up\s+to)\s*(?:(?:KES|KSH)\s*)?([\d,]+(?:\.\d+)?)(?:\s*([kK]))?", request, re.IGNORECASE)
    location_match = re.search(r"(?:\bin\b|\baround\b|\bnear\b)\s+([A-Za-z][A-Za-z' -]*(?:\s+or\s+[A-Za-z][A-Za-z' -]*)?)(?=\s*,|\s+(?:max|maximum|under|up\s+to)\b|$)", request, re.IGNORECASE)
    if not location_match:
        location_match = re.search(r"\d+\s*[- ]?bed(?:room)?s?\s+(?:apartment\s+)?((?!apartment\b)[A-Za-z][A-Za-z' -]*?)(?=\s*,|\s+(?:max|maximum|under|up\s+to)\b|$)", request, re.IGNORECASE)
    if not beds_match and not location_match:
        raise ValueError("Try: 2 bedroom apartment in Westlands under KSh 85000, with parking")
    known = ["parking", "security", "secure", "furnished", "balcony", "pool", "gym", "near public transport"]
    must_haves = [item for item in known if item in request.lower()]
    location = location_match.group(1).strip() if location_match and location_match.lastindex else ""
    location_raw = (location_match.group(0).strip() if location_match and re.match(r"(?:in|around|near)\b", location_match.group(0), re.IGNORECASE) else location) if location_match else ""
    locations = [part.strip() for part in re.split(r"\s+or\s+|\s+and\s+", location, flags=re.IGNORECASE) if part.strip()]
    location = locations[0] if locations else location
    lowered = request.lower()
    transaction_type = TransactionType.RENT_MONTHLY
    if re.search(r"\b(?:for sale|to buy|buy|land)\b", lowered):
        transaction_type = TransactionType.LAND_SALE if "land" in lowered else TransactionType.SALE
    elif re.search(r"\b(?:short[- ]?let|daily|per day)\b", lowered):
        transaction_type = TransactionType.SHORT_LET if "short" in lowered else TransactionType.RENT_DAILY
    amount = float(rent_match.group(1).replace(",", "")) if rent_match else None
    if amount is not None and rent_match.group(2):
        amount *= 1000
    return SearchCriteria(beds=int(beds_match.group(1)) if beds_match else None, location=location, location_raw=location_raw or request, locations=locations, max_rent=int(amount) if amount is not None else None, must_haves=must_haves, transaction_type=transaction_type)


if __name__ == "__main__":
    request = " ".join(sys.argv[1:])
    if not request:
        request = input("What home are you looking for? ")
    try:
        result = run(parse_request(request))
        print(json.dumps(to_jsonable(result), indent=2))
        print(f"\nHTML report: {write_report(result).resolve()}")
    except Exception as error:
        print(f"Tuhame stopped safely: {error}")
        raise SystemExit(1)
