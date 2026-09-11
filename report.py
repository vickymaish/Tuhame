"""Generate a small evidence-first HTML briefing."""
from html import escape
from pathlib import Path

from schemas import PipelineResult


def _evidence(listing) -> str:
    rows = []
    for item in listing.evidence:
        evidence = item.evidence_text or "No source text found"
        rows.append(f"<li><strong>{escape(item.claim)}</strong>: {escape(str(item.value))} "
                    f"<span class='status {item.status.value.lower()}'>{item.status.value}</span> "
                    f"<q>{escape(evidence)}</q></li>")
    return "<ul>" + "".join(rows) + "</ul>" if rows else "<p>Evidence unavailable.</p>"


def render_report(result: PipelineResult) -> str:
    cards = []
    for survivor in result.survivors:
        listing = survivor.listing
        images = "".join(
            f"<a href='{escape(url)}' target='_blank' rel='noreferrer'><img src='{escape(url)}' alt='Listing photo' loading='lazy'></a>"
            for url in listing.image_urls
        ) or "<p class='muted'>No source image URL found.</p>"
        source = f"<a href='{escape(listing.url)}' target='_blank' rel='noreferrer'>Open source listing</a>" if listing.url else "Source URL unavailable"
        contacts = "".join(f"<li><strong>{escape(str(contact.type or contact.kind))}</strong>: {escape(str(contact.value or 'Number not established'))} <small>{escape(str(contact.contact_scope))}</small></li>" for contact in listing.contacts)
        cards.append(f"""
        <article class='listing'>
          <div class='photos'>{images}</div>
          <h2>{escape(listing.location or 'Location unknown')} · {escape(str(listing.beds or '?'))} bedrooms</h2>
          <p class='rent'>KSh {listing.rent:,} <small>source-extracted rent</small></p>
          <p>{escape(source)}</p>
          <p>{escape(listing.freshness.explanation)}</p>
          <h3>Contactability</h3><p>{escape(str(listing.contactability))}</p><ul>{contacts or '<li>No public contact method established.</li>'}</ul>
          <h3>Evidence</h3>{_evidence(listing)}
          <h3>Why it survived</h3><ul>{''.join(f'<li>{escape(reason)}</li>' for reason in survivor.match_reasons)}</ul>
          {('<h3>Verification actions</h3><ul>' + ''.join(f'<li>{escape(action)}</li>' for action in survivor.verification.required_actions) + '</ul>') if survivor.verification and survivor.verification.required_actions else ''}
          {'<h3>Flags</h3><ul>' + ''.join(f'<li>{escape(flag)}</li>' for flag in survivor.red_flags) + '</ul>' if survivor.red_flags else ''}
        </article>
        """)
    rejected = "".join(f"<li>{escape(item.get('reason', 'Rejected'))} <small>{escape(item.get('url') or '')}</small></li>" for item in result.rejected)
    return f"""<!doctype html>
<html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Nyumba Hunter briefing</title><style>
:root{{font-family:system-ui,sans-serif;color:#18221d;background:#f4f1e8}}body{{max-width:1100px;margin:0 auto;padding:32px}}h1{{margin-bottom:4px}}.muted,small{{color:#69746d}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:20px}}.listing{{background:white;border:1px solid #d7ddd4;border-radius:8px;padding:18px;box-shadow:0 4px 14px #243b2b12}}.photos{{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;min-height:72px}}.photos img{{width:100%;height:110px;object-fit:cover;border-radius:4px}}.rent{{font-size:1.5rem;font-weight:700;margin:8px 0}}.status{{font-size:.72rem;padding:2px 5px;border-radius:3px;background:#e5eee5}}.conflict{{background:#f6d5c8}}.unknown,.unverified{{background:#f5e8b7}}q{{color:#536158}}a{{color:#17633c}}.rejected{{background:#fff8f5;border:1px solid #efd6cb;padding:16px}}
</style></head><body><h1>Nyumba Hunter briefing</h1>
<p>{result.criteria.beds} bedrooms in <strong>{escape(result.criteria.location or 'the requested area')}</strong>{f", maximum KSh {result.criteria.max_rent:,}" if result.criteria.max_rent is not None else ", budget not specified"}</p>
<p>Discovered {result.discovered} listings · Removed {result.duplicates_removed} duplicates · Shortlisted {len(result.survivors)}</p>
<section class='grid'>{''.join(cards) or '<p>No listings survived the evidence and budget checks.</p>'}</section>
<section class='rejected'><h2>Rejected or requiring verification</h2><ul>{rejected or '<li>None</li>'}</ul></section>
</body></html>"""


def write_report(result: PipelineResult, path: str = "report.html") -> Path:
    output = Path(path)
    output.write_text(render_report(result), encoding="utf-8")
    return output