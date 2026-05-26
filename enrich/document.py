"""The enriched, typed document we store per contact name."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EnrichedDoc:
    raw: str
    type: str = "person"                       # person | org | unknown
    names: list[dict] = field(default_factory=list)    # {text,script,ipa,key}
    orgs: list[dict] = field(default_factory=list)     # {text,script,ipa,key}
    anchors: list[dict] = field(default_factory=list)  # name governed by a role
    roles: list[str] = field(default_factory=list)     # canonical role labels
    context: list[dict] = field(default_factory=list)  # {text,kind}
    dropped: list[str] = field(default_factory=list)   # emoji/years/numbers

    # --- derived flat fields for ES (set by finalize) ---
    name_ipa: list[str] = field(default_factory=list)
    name_keys: list[str] = field(default_factory=list)
    org_ipa: list[str] = field(default_factory=list)
    anchor_keys: list[str] = field(default_factory=list)

    def finalize(self) -> "EnrichedDoc":
        self.name_ipa = [n["ipa"] for n in self.names if n["ipa"]]
        self.name_keys = sorted({n["key"] for n in self.names if n["key"]})
        self.org_ipa = [o["ipa"] for o in self.orgs if o["ipa"]]
        self.anchor_keys = sorted({a["key"] for a in self.anchors if a["key"]})
        return self

    def to_es(self) -> dict:
        """Flat document for the Elasticsearch index."""
        return {
            "raw": self.raw,
            "type": self.type,
            "name_text": " ".join(n["text"] for n in self.names
                                   if n.get("via") != "nickname"),
            "name_ipa": self.name_ipa,
            "name_keys": self.name_keys,
            "org_text": " ".join(o["text"] for o in self.orgs),
            "org_ipa": self.org_ipa,
            "roles": self.roles,
            "anchor_ipa": [a["ipa"] for a in self.anchors if a["ipa"]],
            "anchor_keys": self.anchor_keys,
            "context": [c["text"] for c in self.context],
        }
