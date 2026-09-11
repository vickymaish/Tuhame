"""Historical observations of listings, separate from publication dates."""
from datetime import datetime, timezone

from tools.cache import _connection


def record_observation(url: str, observed_at: datetime | None = None) -> dict:
    observed_at = observed_at or datetime.now(timezone.utc)
    value = observed_at.isoformat()
    with _connection() as connection:
        connection.execute("CREATE TABLE IF NOT EXISTS listing_observations (url TEXT PRIMARY KEY, first_seen TEXT NOT NULL, last_seen TEXT NOT NULL, observation_count INTEGER NOT NULL)")
        row = connection.execute("SELECT first_seen, observation_count FROM listing_observations WHERE url = ?", (url,)).fetchone()
        if row:
            connection.execute("UPDATE listing_observations SET last_seen = ?, observation_count = ? WHERE url = ?", (value, row[1] + 1, url))
            first_seen, count = row[0], row[1] + 1
        else:
            connection.execute("INSERT INTO listing_observations VALUES (?, ?, ?, ?)", (url, value, value, 1))
            first_seen, count = value, 1
    return {"first_seen": first_seen, "last_seen": value, "observation_count": count, "observed_online_for_days": (observed_at - datetime.fromisoformat(first_seen)).days}
