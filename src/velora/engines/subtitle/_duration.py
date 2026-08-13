"""Measuring an audio clip's real duration.

Uses `mutagen <https://mutagen.readthedocs.io/>`_ to read container
metadata (not to decode the audio itself) — fast, and works on the
in-memory ``bytes`` a :class:`~velora.engines.narration_audio.SceneAudio`
already holds, with no filename or format hint required: mutagen
detects the container from its own magic bytes.

``mutagen`` is a required dependency of `velora` itself (ADR-0022),
not an optional extra like `anthropic`/`elevenlabs`/`openai`: it is
generic infrastructure the Core needs to do its own job correctly, not
a vendor SDK behind a swappable Provider.
"""

from __future__ import annotations

import io

import mutagen

__all__ = ["measure_duration_seconds"]


def measure_duration_seconds(audio: bytes) -> float | None:
    """Return ``audio``'s duration in seconds, or ``None`` if it
    couldn't be determined.

    Returns ``None`` — rather than raising — for any audio mutagen
    can't parse: an unsupported or corrupt container, or arbitrary
    bytes that aren't audio at all. A `VoiceProvider` is code `velora`
    doesn't control (ADR-0009); this function's caller
    (:class:`~velora.engines.subtitle.SubtitleEngine`) is expected to
    fall back to an estimate rather than let one Provider's unusual
    encoding abort the whole Story.
    """
    try:
        parsed = mutagen.File(io.BytesIO(audio))
    except Exception:
        # mutagen's own exception surface for malformed input isn't narrow
        # or fully documented; any failure here means "couldn't determine
        # duration", handled identically regardless of its exact cause.
        return None

    if parsed is None or parsed.info is None:
        return None

    length = parsed.info.length
    return float(length) if length is not None else None
