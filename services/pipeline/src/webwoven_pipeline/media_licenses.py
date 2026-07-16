from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MediaLicenseSpec:
    identifier: str
    label: str
    canonical_url: str
    requires_creator: bool
    share_alike: bool = False


def _cc(
    identifier: str,
    label: str,
    path: str,
    *,
    share_alike: bool = False,
) -> MediaLicenseSpec:
    return MediaLicenseSpec(
        identifier,
        label,
        f"https://creativecommons.org/licenses/{path}/",
        requires_creator=True,
        share_alike=share_alike,
    )


LICENSE_SPECS = {
    "PUBLIC_DOMAIN": MediaLicenseSpec(
        "PUBLIC_DOMAIN",
        "Public Domain",
        "https://creativecommons.org/publicdomain/mark/1.0/",
        requires_creator=False,
    ),
    "CC0_1_0": MediaLicenseSpec(
        "CC0_1_0",
        "CC0 1.0",
        "https://creativecommons.org/publicdomain/zero/1.0/",
        requires_creator=False,
    ),
    "CC_BY_1_0": _cc("CC_BY_1_0", "CC BY 1.0", "by/1.0"),
    "CC_BY_2_0": _cc("CC_BY_2_0", "CC BY 2.0", "by/2.0"),
    "CC_BY_2_5": _cc("CC_BY_2_5", "CC BY 2.5", "by/2.5"),
    "CC_BY_3_0": _cc("CC_BY_3_0", "CC BY 3.0", "by/3.0"),
    "CC_BY_4_0": _cc("CC_BY_4_0", "CC BY 4.0", "by/4.0"),
    "CC_BY_SA_1_0": _cc("CC_BY_SA_1_0", "CC BY-SA 1.0", "by-sa/1.0", share_alike=True),
    "CC_BY_SA_2_0": _cc("CC_BY_SA_2_0", "CC BY-SA 2.0", "by-sa/2.0", share_alike=True),
    "CC_BY_SA_2_5": _cc("CC_BY_SA_2_5", "CC BY-SA 2.5", "by-sa/2.5", share_alike=True),
    "CC_BY_SA_3_0": _cc("CC_BY_SA_3_0", "CC BY-SA 3.0", "by-sa/3.0", share_alike=True),
    "CC_BY_SA_4_0": _cc("CC_BY_SA_4_0", "CC BY-SA 4.0", "by-sa/4.0", share_alike=True),
}

SUPPORTED_LICENSE_IDS = frozenset(LICENSE_SPECS)


def license_id_from_short_name(raw: str) -> str | None:
    normalized = re.sub(r"[^a-z0-9]+", " ", raw.casefold()).strip()
    if normalized in {"public domain", "pd"}:
        return "PUBLIC_DOMAIN"
    if normalized in {"cc0", "cc0 1 0"}:
        return "CC0_1_0"
    match = re.fullmatch(
        r"cc by( sa)? (1 0|2 0|2 5|3 0|4 0)(?: [a-z]{2,3})?",
        normalized,
    )
    if match is None:
        return None
    family = "CC_BY_SA" if match.group(1) else "CC_BY"
    version = match.group(2).replace(" ", "_")
    identifier = f"{family}_{version}"
    return identifier if identifier in LICENSE_SPECS else None


def license_spec(identifier: str) -> MediaLicenseSpec | None:
    return LICENSE_SPECS.get(identifier)
