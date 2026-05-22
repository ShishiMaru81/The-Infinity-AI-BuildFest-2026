"""Map model labels to canonical hazard classes: knife, gun, fire, lighter."""

HAZARD_CLASSES = ("knife", "gun", "fire", "lighter")

# Keywords per canonical class (matched case-insensitively on raw label)
LABEL_KEYWORDS: dict[str, tuple[str, ...]] = {
    "knife": ("knife", "blade", "dagger", "machete", "sword"),
    "gun": (
        "gun",
        "pistol",
        "rifle",
        "firearm",
        "weapon",
        "handgun",
        "shotgun",
        "revolver",
        "ak47",
        "ar15",
    ),
    "fire": ("fire", "flame", "smoke", "burning", "bonfire"),
    "lighter": ("lighter", "match", "matches", "igniter", "bic"),
}

INCIDENT_BY_HAZARD = {
    "knife": "WEAPON_DETECTED",
    "gun": "WEAPON_DETECTED",
    "lighter": "WEAPON_DETECTED",
    "fire": "FIRE",
}

PRIORITY_BY_HAZARD = {
    "knife": "CRITICAL",
    "gun": "CRITICAL",
    "lighter": "HIGH",
    "fire": "CRITICAL",
}


def normalize_label(raw: str) -> str | None:
    low = raw.lower().strip().replace("_", " ")
    for hazard, keywords in LABEL_KEYWORDS.items():
        if low == hazard or any(kw in low for kw in keywords):
            return hazard
    return None
