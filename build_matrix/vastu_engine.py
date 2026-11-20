"""
BuildMetrics AI — Vastu Shastra & Spatial Harmony Orientation Engine
Comprehensive architectural directional zone audits (9-sector Vastu Purusha Mandala),
elemental balance (Pancha Bhoota), scientific bio-climatic rationales, and non-destructive remedies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from build_matrix.models import BuildingModel


@dataclass
class VastuRemedyKit:
    """Actionable three-tier non-destructive remedy suite for a specific room or zone."""
    furniture_remedy: str
    color_therapy: str
    elemental_cure: str
    energy_neutralizer: str


@dataclass
class VastuRoomAudit:
    """Detailed directional audit of an individual room within the Vastu Purusha Mandala."""
    room_id: str
    room_name: str
    zone: str                       # e.g. "North-East (Ishanya)", "South-East (Agni)"
    ideal_zones: list[str]          # Top recommended zones for this room type
    compliance: str                 # "Ideal", "Favorable", "Neutral", "Non-Compliant"
    score: int                      # 0 to 100
    remedy: str                     # Primary actionable recommendation (backward-compatible)
    element: str = "Space (Akash)"  # Pancha Bhoota element of the zone
    ruling_energy: str = "Cosmic"   # Deity / energy lord associated with zone
    scientific_rationale: str = ""  # Solar geometry & geomagnetic justification
    dosha_severity: str = "None"    # "None", "Minor", "Moderate", "Severe", "Critical"
    dosha_name: str = ""            # Identified architectural imbalance (if any)
    recommended_colors: str = ""    # Color therapy palette
    interior_tips: list[str] = field(default_factory=list)  # Step-by-step layout suggestions
    remedy_kit: VastuRemedyKit | None = None


@dataclass
class VastuZoneDetail:
    """Architectural and metaphysical attributes of one of the 9 Vastu mandala sectors."""
    sector_key: str                 # e.g. "NE", "E", "SE", "S", "SW", "W", "NW", "N", "Center"
    sector_name: str                # e.g. "North-East (Ishanya)"
    element: str                    # Water, Fire, Earth, Air, Space
    ruling_deity: str               # e.g. "Lord Shiva / Brihaspati (Jupiter)"
    compass_bearing: str            # e.g. "22.5° to 67.5°"
    bio_climatic_role: str          # Scientific rationale (solar, thermal, magnetic)
    life_aspect: str                # Health, Wealth, Clarity, Longevity, Stability
    ideal_uses: list[str]           # Best room allocations
    forbidden_uses: list[str]       # Imbalanced allocations to avoid
    color_palette: str              # Recommended shades and wall accents
    occupant_rooms: list[str] = field(default_factory=list)
    sector_score: int = 100
    status_icon: str = "🟢"


@dataclass
class VastuReport:
    """Comprehensive spatial harmony audit report for clients, architects, and homeowners."""
    overall_score: int                          # 0 to 100
    grade: str                                  # A+ Auspicious, A Harmonious, B Balanced, C Needs Remedial Cures
    brahmasthan_status: str                     # "Clear & Open (Auspicious Energy Core)" or "Encumbered"
    element_scores: dict[str, int]              # Water, Fire, Earth, Air, Space (0-100)
    room_audits: list[VastuRoomAudit]
    key_recommendations: list[str]
    # Enhanced attributes for customer presentation
    zone_matrix: dict[str, VastuZoneDetail] = field(default_factory=dict)
    doshas_identified: list[dict[str, str]] = field(default_factory=list)
    customer_executive_summary: str = ""
    scientific_foundations: list[dict[str, str]] = field(default_factory=list)
    actionable_checklist: list[str] = field(default_factory=list)
    entrance_audit: dict[str, Any] = field(default_factory=dict)

    @property
    def recommendations(self) -> list[str]:
        return self.key_recommendations

    @property
    def rating(self) -> str:
        return self.grade

    @property
    def simha_dwara_status(self) -> dict[str, Any]:
        return self.entrance_audit


class VastuEngine:
    """
    Evaluates 9-zone directional harmony according to traditional Vastu Shastra
    coupled with modern bio-climatic, solar-path, and geomagnetic building science.
    """

    # 3x3 Grid Sector Definitions (gx: 0=West, 1=Center, 2=East; gy: 0=South, 1=Center, 2=North)
    ZONES: dict[tuple[int, int], str] = {
        (0, 2): "North-West (Vayavya)",
        (1, 2): "North (Uttara)",
        (2, 2): "North-East (Ishanya)",
        (0, 1): "West (Paschim)",
        (1, 1): "Brahmasthan (Center)",
        (2, 1): "East (Purva)",
        (0, 0): "South-West (Nairutya)",
        (1, 0): "South (Dakshina)",
        (2, 0): "South-East (Agni)",
    }

    ZONE_SECTOR_KEYS: dict[str, str] = {
        "North-East (Ishanya)": "NE",
        "North (Uttara)": "N",
        "North-West (Vayavya)": "NW",
        "East (Purva)": "E",
        "Brahmasthan (Center)": "Center",
        "West (Paschim)": "W",
        "South-East (Agni)": "SE",
        "South (Dakshina)": "S",
        "South-West (Nairutya)": "SW",
    }

    SECTOR_METADATA: dict[str, dict[str, Any]] = {
        "NE": {
            "name": "North-East (Ishanya)",
            "element": "Water (Jal)",
            "deity": "Lord Shiva & Brihaspati (Jupiter)",
            "bearing": "22.5° to 67.5°",
            "bio_climatic": "Receives morning solar UV-A radiation (germicidal, vitamin-D synthesizing) with lowest thermal gain. Coolest corner requiring maximum light and openness.",
            "life_aspect": "Spiritual prana, mental clarity, wisdom, neurological health, and cosmic intuition.",
            "ideal": ["Pooja / Temple", "Meditation Room", "Underground Water Tank / Sump", "Living Room", "Study / Library", "Open Lawn"],
            "forbidden": ["Master Bedroom", "Kitchen / Fire", "Toilet / Septic Tank", "Heavy Overhead Water Tank", "Staircase"],
            "colors": "White, Off-White, Baby Blue, Mint Cream, Light Silver",
        },
        "N": {
            "name": "North (Uttara)",
            "element": "Water / Earth Gradient",
            "deity": "Lord Kubera & Budha (Mercury)",
            "bearing": "337.5° to 22.5°",
            "bio_climatic": "Receives soft, diffuse daylight without direct thermal heating. Geomagnetically aligned with Earth's North pole attraction.",
            "life_aspect": "Financial growth, cash flow liquidity, career advancement, and new opportunities.",
            "ideal": ["Living Room", "Treasury / Safe", "Entrance Gate", "Study / Home Office", "Balcony / Verandah"],
            "forbidden": ["Heavy Storage", "Toilet", "Master Bedroom", "Staircase", "Kitchen"],
            "colors": "Light Green, Seafoam, Pista, White, Ivory",
        },
        "NW": {
            "name": "North-West (Vayavya)",
            "element": "Air (Vayu)",
            "deity": "Lord Vayu & Chandra (Moon)",
            "bearing": "292.5° to 337.5°",
            "bio_climatic": "Subject to evening prevailing winds and changing thermal currents. Natural movement and dynamic aeration zone.",
            "life_aspect": "Social relationships, guest relations, mobility, helpful allies, and travel.",
            "ideal": ["Guest Bedroom", "Children's Bedroom", "Dining Room", "Bathroom / Washroom", "Pantry / Finished Goods"],
            "forbidden": ["Master Bedroom (creates restlessness)", "Pooja Room", "Heavy Safe", "Basement"],
            "colors": "Cream, Pearl White, Soft Grey, Light Silver",
        },
        "E": {
            "name": "East (Purva)",
            "element": "Solar Fire / Water Gradient",
            "deity": "Lord Indra & Surya (Sun)",
            "bearing": "67.5° to 112.5°",
            "bio_climatic": "Point of sunrise. Inundated with early infrared and circadian-regulating dawn light. Requires ample windows and low sill heights.",
            "life_aspect": "Vitality, leadership, social fame, cardiovascular health, and masculine vital prana.",
            "ideal": ["Living Room", "Main Entrance", "Study", "Children's Room", "Balcony", "Garden / Patio"],
            "forbidden": ["Toilet", "Heavy Storage", "Master Bedroom", "Septic Tank"],
            "colors": "Light Yellow, Sunlight Gold, Cream, Sage Green",
        },
        "Center": {
            "name": "Brahmasthan (Center)",
            "element": "Space (Akash)",
            "deity": "Lord Brahma (The Creator)",
            "bearing": "Core central 1/9th zone",
            "bio_climatic": "Central architectural nexus. Provides cross-ventilation chimney effect and spatial acoustic equilibrium. Must remain lightweight and uncluttered.",
            "life_aspect": "Overall holistic harmony, inner peace, family unity, and atmospheric resonance.",
            "ideal": ["Open Courtyard (Atrium)", "Central Foyer", "Light Skylight", "Meditation Circle"],
            "forbidden": ["Structural Pillars", "Staircase", "Toilet / Septic Tank", "Kitchen / Flame", "Heavy Walls"],
            "colors": "Pure White, Light Ivory, Golden Champagne, Soft Beige",
        },
        "W": {
            "name": "West (Paschim)",
            "element": "Air / Water Gradient",
            "deity": "Lord Varuna & Shani (Saturn)",
            "bearing": "247.5° to 292.5°",
            "bio_climatic": "Receives intense late afternoon infrared radiation. Requires moderate thermal mass and medium-sized shading openings.",
            "life_aspect": "Material gains, business profits, sustained prosperity, fulfillment of desires, and discipline.",
            "ideal": ["Dining Room", "Children's Bedroom", "Study", "Overhead Water Tank", "Staircase"],
            "forbidden": ["Pooja / Temple", "Underground Sump / Borewell", "Main Entrance (unless Pushpadanta pad)"],
            "colors": "Soft Blue, Slate Grey, Beige, Muted White",
        },
        "SE": {
            "name": "South-East (Agni)",
            "element": "Fire (Agni)",
            "deity": "Lord Agni & Shukra (Venus)",
            "bearing": "112.5° to 157.5°",
            "bio_climatic": "Receives mid-morning to noon intense solar irradiation. High ambient heat potential, ideal for cooking combustion and electrical transformers.",
            "life_aspect": "Metabolic health, digestive power, passion, financial liquidity, and reproductive vitality.",
            "ideal": ["Kitchen (Primary)", "Electrical Main Panel / Inverter", "Generator / Geyser", "Gym / Fitness Area"],
            "forbidden": ["Master Bedroom", "Pooja Room", "Underground Water Tank", "Bathroom / Toilet"],
            "colors": "Pastel Pink, Coral, Peach, Light Orange, Cream",
        },
        "S": {
            "name": "South (Dakshina)",
            "element": "Earth / Fire Gradient",
            "deity": "Lord Yama & Mangala (Mars)",
            "bearing": "157.5° to 202.5°",
            "bio_climatic": "High thermal solar radiation throughout mid-day. Thicker walls and vertical shading provide passive thermal resistance.",
            "life_aspect": "Courage, reputation, legal stability, restorative deep sleep, and stamina.",
            "ideal": ["Bedroom", "Staircase", "Heavy Storage / Wardrobes", "Overhead Tank"],
            "forbidden": ["Main Entrance (unless specific pada)", "Underground Water Tank", "Pooja Room"],
            "colors": "Terracotta, Earthy Brown, Warm Ochre, Sandstone",
        },
        "SW": {
            "name": "South-West (Nairutya)",
            "element": "Earth (Prithvi)",
            "deity": "Lord Nirriti & Rahu",
            "bearing": "202.5° to 247.5°",
            "bio_climatic": "Heaviest solar thermal exposure during peak afternoon. Highest thermal inertia and highest ground mass required to anchor building balance.",
            "life_aspect": "Stability, leadership, relationship bonding, family head authority, and financial grounding.",
            "ideal": ["Master Bedroom (Supreme)", "Heavy Wardrobes / Safe", "Overhead Water Tank", "Staircase", "Store Room"],
            "forbidden": ["Kitchen / Fire", "Pooja Room", "Underground Sump / Borewell", "Toilet / Septic Tank", "Large Windows / Balcony"],
            "colors": "Earthy Yellow, Biscuit, Mustard, Warm Camel, Terracotta",
        },
    }

    IDEAL_ALLOCATIONS: dict[str, list[str]] = {
        "living": ["North-East (Ishanya)", "North (Uttara)", "East (Purva)", "North-West (Vayavya)"],
        "master": ["South-West (Nairutya)", "South (Dakshina)", "West (Paschim)"],
        "bedroom": ["South-West (Nairutya)", "South (Dakshina)", "West (Paschim)", "North-West (Vayavya)"],
        "kitchen": ["South-East (Agni)", "North-West (Vayavya)"],
        "study": ["North-East (Ishanya)", "North (Uttara)", "East (Purva)", "West (Paschim)"],
        "pooja": ["North-East (Ishanya)", "North (Uttara)", "East (Purva)"],
        "dining": ["West (Paschim)", "East (Purva)", "North (Uttara)", "South-East (Agni)"],
        "staircase": ["South (Dakshina)", "West (Paschim)", "South-West (Nairutya)"],
        "bathroom": ["North-West (Vayavya)", "West (Paschim)", "South (Dakshina)"],
        "balcony": ["North-East (Ishanya)", "North (Uttara)", "East (Purva)"],
        "utility": ["South-East (Agni)", "North-West (Vayavya)", "West (Paschim)"],
        "store": ["South-West (Nairutya)", "South (Dakshina)", "West (Paschim)"],
    }

    @classmethod
    def audit_building(cls, building: BuildingModel) -> VastuReport:
        """
        Executes a holistic architectural Vastu Shastra audit for the entire building model.
        Evaluates room coordinates, entrance doors, columns in Brahmasthan, and elemental distribution.
        """
        plot = building.plot
        length, width = max(float(plot.length), 1.0), max(float(plot.width), 1.0)
        room_audits: list[VastuRoomAudit] = []
        doshas_identified: list[dict[str, str]] = []

        total_score = 0
        scored_rooms = 0

        # Element tracking
        element_hits = {
            "Water (Jal)": 0,
            "Fire (Agni)": 0,
            "Earth (Prithvi)": 0,
            "Air (Vayu)": 0,
            "Space (Akash)": 0,
        }
        element_totals = {
            "Water (Jal)": 1,
            "Fire (Agni)": 1,
            "Earth (Prithvi)": 1,
            "Air (Vayu)": 1,
            "Space (Akash)": 1,
        }

        # Initialize zone occupancy dictionary
        zone_occupancy: dict[str, list[str]] = {s_key: [] for s_key in cls.SECTOR_METADATA}

        for r in building.rooms:
            # Normalized centroid coordinates (0.0 to 1.0)
            cx = (float(r.x) + float(r.width) / 2.0) / length
            cy = (float(r.y) + float(r.height) / 2.0) / width

            # 3x3 Grid indexing
            gx = min(2, max(0, int(cx * 3)))
            gy = min(2, max(0, int(cy * 3)))
            zone = cls.ZONES.get((gx, gy), "Brahmasthan (Center)")
            sector_key = cls.ZONE_SECTOR_KEYS.get(zone, "Center")
            meta = cls.SECTOR_METADATA.get(sector_key, cls.SECTOR_METADATA["Center"])

            zone_occupancy[sector_key].append(r.name)

            # Classify room type
            r_type = (getattr(r, "room_type", "") or "").lower()
            r_name_lower = (getattr(r, "name", "") or "").lower()
            key_match = None
            for k in cls.IDEAL_ALLOCATIONS:
                if k in r_type or k in r_name_lower:
                    key_match = k
                    break
            if not key_match:
                key_match = "bedroom" if "bed" in (r_type + r_name_lower) else "living"

            ideal = cls.IDEAL_ALLOCATIONS.get(key_match, ["North (Uttara)"])

            # Compute compliance, score, dosha and remedy kit
            audit_result = cls._evaluate_room_placement(
                room_id=r.id,
                room_name=r.name,
                key_match=key_match,
                zone=zone,
                sector_key=sector_key,
                ideal=ideal,
                meta=meta,
            )

            if audit_result.dosha_severity in ("Moderate", "Severe", "Critical"):
                doshas_identified.append({
                    "room": r.name,
                    "zone": zone,
                    "severity": audit_result.dosha_severity,
                    "dosha": audit_result.dosha_name,
                    "remedy": audit_result.remedy,
                })

            # Element balance accounting
            el_name = meta["element"]
            for prime_el in ("Water (Jal)", "Fire (Agni)", "Earth (Prithvi)", "Air (Vayu)", "Space (Akash)"):
                if prime_el.split()[0] in el_name:
                    element_totals[prime_el] += 1
                    if audit_result.score >= 75:
                        element_hits[prime_el] += 1

            total_score += audit_result.score
            scored_rooms += 1
            room_audits.append(audit_result)

        # -------------------------------------------------------------
        # Brahmasthan (Center 20% Core) Audit
        # -------------------------------------------------------------
        center_x_min, center_x_max = length * 0.4, length * 0.6
        center_y_min, center_y_max = width * 0.4, width * 0.6
        central_pillars = [
            p for p in getattr(building, "pillars", [])
            if center_x_min <= float(p.x) <= center_x_max and center_y_min <= float(p.y) <= center_y_max
        ]
        if central_pillars:
            brahmasthan_status = f"Encumbered by {len(central_pillars)} central structural column(s) (Pillar Load)"
            brahmasthan_score = 60
            doshas_identified.append({
                "room": "Brahmasthan (Core)",
                "zone": "Center",
                "severity": "Moderate",
                "dosha": "Structural load in cosmic Brahmasthan core restricts central space expansion",
                "remedy": "Wrap pillars in light ivory or mirrored cladding; install soft upward illumination (uplighting) to spiritually lighten mass.",
            })
        else:
            brahmasthan_status = "Clear & Open (Auspicious Energy Core)"
            brahmasthan_score = 95
            element_hits["Space (Akash)"] += 1

        # -------------------------------------------------------------
        # Entrance & Main Gate Audit
        # -------------------------------------------------------------
        entrance_audit = cls._audit_entrances(building, length, width)
        if entrance_audit.get("dosha"):
            doshas_identified.append({
                "room": "Main Entrance Gate",
                "zone": entrance_audit.get("zone", "South-West"),
                "severity": entrance_audit.get("severity", "Moderate"),
                "dosha": entrance_audit["dosha"],
                "remedy": entrance_audit.get("remedy", "Install a brass threshold strip and auspicious copper pyramid."),
            })

        # Calculate final overall score (weighted 80% rooms, 15% Brahmasthan, 5% entrance)
        entrance_score = entrance_audit.get("score", 85)
        raw_overall = (
            (total_score / max(1, scored_rooms)) * 0.80
            + (brahmasthan_score * 0.15)
            + (entrance_score * 0.05)
        )
        overall_score = int(min(100, max(30, round(raw_overall))))

        if overall_score >= 85:
            grade = "A+ Auspicious"
        elif overall_score >= 75:
            grade = "A Harmonious"
        elif overall_score >= 60:
            grade = "B Balanced"
        else:
            grade = "C Needs Remedial Cures"

        # Final element scores (0 - 100)
        element_scores = {
            k: int(min(100, max(45, (element_hits[k] / max(1, element_totals[k])) * 100 + 35)))
            for k in element_hits
        }

        # Build 9-zone detailed matrix
        zone_matrix: dict[str, VastuZoneDetail] = {}
        for s_key, s_data in cls.SECTOR_METADATA.items():
            occupants = zone_occupancy.get(s_key, [])
            # Sector score based on occupants
            occ_audits = [a for a in room_audits if a.zone == s_data["name"]]
            s_score = int(sum(a.score for a in occ_audits) / max(1, len(occ_audits))) if occ_audits else 90
            status_icon = "🟢" if s_score >= 80 else "🟡" if s_score >= 65 else "🔴"

            zone_matrix[s_key] = VastuZoneDetail(
                sector_key=s_key,
                sector_name=s_data["name"],
                element=s_data["element"],
                ruling_deity=s_data["deity"],
                compass_bearing=s_data["bearing"],
                bio_climatic_role=s_data["bio_climatic"],
                life_aspect=s_data["life_aspect"],
                ideal_uses=s_data["ideal"],
                forbidden_uses=s_data["forbidden"],
                color_palette=s_data["colors"],
                occupant_rooms=occupants,
                sector_score=s_score,
                status_icon=status_icon,
            )

        # High-impact key recommendations
        key_recs = cls._generate_key_recommendations(room_audits, central_pillars, entrance_audit)

        # Actionable customer checklist
        actionable_checklist = cls._generate_actionable_checklist(room_audits, central_pillars, entrance_audit)

        # Executive narrative summary
        exec_summary = cls._generate_executive_summary(overall_score, grade, room_audits, doshas_identified)

        # Scientific foundations explainer
        scientific_foundations = cls._get_scientific_foundations()

        return VastuReport(
            overall_score=overall_score,
            grade=grade,
            brahmasthan_status=brahmasthan_status,
            element_scores=element_scores,
            room_audits=room_audits,
            key_recommendations=key_recs,
            zone_matrix=zone_matrix,
            doshas_identified=doshas_identified,
            customer_executive_summary=exec_summary,
            scientific_foundations=scientific_foundations,
            actionable_checklist=actionable_checklist,
            entrance_audit=entrance_audit,
        )

    # ---------------------------------------------------------------------------
    # Private Helper Evaluation Methods
    # ---------------------------------------------------------------------------

    @classmethod
    def _evaluate_room_placement(
        cls,
        room_id: str,
        room_name: str,
        key_match: str,
        zone: str,
        sector_key: str,
        ideal: list[str],
        meta: dict[str, Any],
    ) -> VastuRoomAudit:
        """Evaluates an individual room's placement against bio-climatic and Vastu principles."""
        ideal_zone_match = ideal[0] if ideal else "North (Uttara)"

        # Check compliance tier
        if zone == ideal_zone_match:
            compliance = "Ideal"
            score = 100
            remedy = f"Optimal placement in {zone}. Maximizes positive directional energy flow and bio-climatic synergy."
            dosha_severity = "None"
            dosha_name = ""
        elif zone in ideal:
            compliance = "Favorable"
            score = 80
            remedy = f"Harmonious placement in {zone}. Maintain recommended wall palette and keep airflow unobstructed."
            dosha_severity = "Minor"
            dosha_name = f"Secondary zone allocation ({zone} instead of primary {ideal[0]})"
        elif zone == "Brahmasthan (Center)":
            compliance = "Neutral"
            score = 65
            remedy = "Keep room central zone open and ensure adequate overhead natural lighting; avoid placing heavy fixed furniture in the middle."
            dosha_severity = "Moderate"
            dosha_name = "Core placement encroaching Brahmasthan center"
        else:
            compliance = "Non-Compliant"
            score = 40
            dosha_severity, dosha_name, remedy = cls._diagnose_specific_dosha(key_match, zone)

        # Scientific explanation
        scientific_rationale = cls._get_scientific_rationale(key_match, zone, compliance)

        # Specific remedy kit
        remedy_kit = cls._build_remedy_kit(key_match, zone, compliance)

        # Interior tips
        interior_tips = cls._get_interior_tips(key_match, zone)

        return VastuRoomAudit(
            room_id=room_id,
            room_name=room_name,
            zone=zone,
            ideal_zones=ideal,
            compliance=compliance,
            score=score,
            remedy=remedy,
            element=meta["element"],
            ruling_energy=meta["deity"],
            scientific_rationale=scientific_rationale,
            dosha_severity=dosha_severity,
            dosha_name=dosha_name,
            recommended_colors=meta["colors"],
            interior_tips=interior_tips,
            remedy_kit=remedy_kit,
        )

    @classmethod
    def _diagnose_specific_dosha(cls, room_type: str, zone: str) -> tuple[str, str, str]:
        """Identifies the classical Vastu Dosha name, severity, and non-destructive remedy."""
        if room_type == "kitchen" and ("Ishanya" in zone or "North-East" in zone):
            return (
                "Critical",
                "Agni-Jal Clash (Fire element trapped in sacred Water sector)",
                "Install a green granite/marble slab under cooktop to introduce the Wood element mediating Fire and Water; paint kitchen walls soft cream or light yellow; keep gas burner strictly in the room's SE corner.",
            )
        if room_type == "kitchen" and ("Nairutya" in zone or "South-West" in zone):
            return (
                "Severe",
                "Agni-Prithvi Disturbance (Fire burning through Earth stability anchor)",
                "Cook facing East; place a yellow jasper crystal pyramid in SW corner; use warm sand/beige wall tiles and avoid dark grey or black finishes.",
            )
        if room_type in ("master", "bedroom") and ("Ishanya" in zone or "North-East" in zone):
            return (
                "Severe",
                "Restless Head of Household (Spiritual zone conflicting with master bedroom)",
                "Sleep with head strictly pointing South; use warm beige, almond, or sandalwood wall hues; keep heavy wooden furniture in the room's SW corner; avoid mirrors facing the bed.",
            )
        if room_type == "bathroom" and ("Ishanya" in zone or "North-East" in zone):
            return (
                "Critical",
                "Ishanya Dushit (Negative drain located in pure cosmic receptor)",
                "Keep bathroom door permanently closed; fix a full-length mirror on outer door surface to reflect energy; place an open bowl of natural Himalayan rock salt inside (replace every 15 days); install a zinc Vastu strip along threshold.",
            )
        if room_type == "bathroom" and ("Nairutya" in zone or "South-West" in zone):
            return (
                "Severe",
                "Nairutya Drainage (Earth stability energy drained by plumbing)",
                "Keep toilet seat down when not in use; place a lead pyramid outside bathroom entrance; use earthy brown and dark beige accents.",
            )
        if room_type == "pooja" and ("Nairutya" in zone or "Dakshina" in zone or "South" in zone):
            return (
                "Moderate",
                "Altar in Heavy Inertia Zone (Pooja placed in heavy Prithvi/Yama sector)",
                "Elevate shrine on a light wooden/marble pedestal off the ground; face deities toward West so devotee faces East during prayer; use pure white or cream backdrops.",
            )
        if room_type == "living" and ("Nairutya" in zone or "South-West" in zone):
            return (
                "Minor",
                "Subdued Social Prana (Living area in private Earth zone)",
                "Maximize lighting using warm 3000K chandeliers; display living indoor plants in North corner of the room; introduce brass metallic accents.",
            )
        return (
            "Moderate",
            f"Sector Discrepancy ({room_type.title()} in {zone})",
            cls._get_remedy(room_type, zone),
        )

    @classmethod
    def _get_remedy(cls, room_type: str, zone: str) -> str:
        """Backward-compatible fallback remedy generator."""
        if room_type == "kitchen":
            return "Place gas burner / cooktop in SE corner of room; cook facing East; utilize warm pastel or cream wall tiles to balance fire energy."
        if room_type in ("master", "bedroom"):
            return "Sleep with head positioned toward South; incorporate earthy tones (terracotta, sandstone, almond) to ground the space; keep wardrobes on SW wall."
        if room_type == "living":
            return "Hang a brass or silver bell near entrance; maximize window ventilation toward North/East; keep central seating area light and open."
        if room_type == "bathroom":
            return "Keep door closed; place an unrefined sea salt bowl in NW corner; seal threshold with a copper or brass divider strip."
        return "Keep the space well-ventilated, uncluttered, and illuminated with warm 3000K daylight LED fixtures."

    @classmethod
    def _get_scientific_rationale(cls, room_type: str, zone: str, compliance: str) -> str:
        """Explains the architectural, solar geometry, and geomagnetic physics behind the audit."""
        if compliance == "Ideal":
            if room_type == "kitchen":
                return "The South-East receives mid-morning solar rays that naturally sanitize cooking surfaces and provide dry air, preventing mold while keeping afternoon radiant heat away from living zones."
            if room_type in ("master", "bedroom"):
                return "The South-West sector is shielded from excessive morning glare and benefits from maximum thermal mass during late afternoon, creating a cool, quiet, and grounded environment for delta-wave sleep."
            if room_type == "living":
                return "The North-East and North quadrants receive gentle, glare-free indirect daylight throughout the day, maintaining a comfortable ambient temperature without high air-conditioning cooling loads."
            if room_type == "pooja":
                return "Early dawn UV-A solar radiation entering North-East stimulates serotonin production and enhances alpha-wave mental concentration during morning meditation."
            return "Optimal balance between solar azimuth angles, diurnal temperature swings, and building cross-ventilation."
        else:
            if "kitchen" in room_type:
                return "Placing cooking appliances in non-fire zones alters the natural thermodynamic exhaust flow, potentially overheating sleeping quarters or competing with morning cool breeze corridors."
            if "bed" in room_type:
                return "Sleeping areas located in active solar or high-ventilation sectors may experience temperature fluctuations and early morning glare, interfering with natural circadian rhythm melatonin cycles."
            return "Non-aligned room orientation can result in higher artificial cooling loads, uneven thermal distribution, or acoustic reverberation."

    @classmethod
    def _build_remedy_kit(cls, room_type: str, zone: str, compliance: str) -> VastuRemedyKit:
        """Generates a complete multi-layered non-destructive remedy toolkit."""
        if compliance == "Ideal":
            return VastuRemedyKit(
                furniture_remedy="Maintain current layout; ensure primary movement pathways remain open and unobstructed.",
                color_therapy="Enhance with natural sector-aligned palette (creams, pastels, or soft whites).",
                elemental_cure="Incorporate fresh indoor greenery or natural woven materials.",
                energy_neutralizer="Ensure adequate natural ventilation and daylight penetration.",
            )
        if room_type == "kitchen":
            return VastuRemedyKit(
                furniture_remedy="Position cooktop against East or South-East wall so cook faces East toward the rising sun.",
                color_therapy="Apply warm off-white, light cream, or peach wall tiles; avoid stark blue, charcoal, or pitch black.",
                elemental_cure="Place a small indoor jade or money plant in North-West corner of the kitchen.",
                energy_neutralizer="Install a copper Agni Vastu strip along the kitchen threshold to insulate fire energy.",
            )
        if room_type in ("master", "bedroom"):
            return VastuRemedyKit(
                furniture_remedy="Position bed headboard strictly against South or West wall (head towards South/East); avoid placing bed directly under ceiling beams.",
                color_therapy="Paint walls in warm champagne, almond, pale terracotta, or light beige.",
                elemental_cure="Keep a grounding rock crystal (rose quartz or raw tourmaline) on the south-west bedside table.",
                energy_neutralizer="Ensure no wardrobe mirrors directly reflect the sleeping bed; cover mirrors at night if unmovable.",
            )
        if room_type == "bathroom":
            return VastuRemedyKit(
                furniture_remedy="Ensure toilet commode is aligned North-South; avoid placing commode facing East or West.",
                color_therapy="Opt for light grey, pale aqua, or crisp white tiles; avoid deep red or dark brown hues.",
                elemental_cure="Keep an open glass bowl filled with unrefined Himalayan sea salt on an upper shelf (replace monthly).",
                energy_neutralizer="Fit an airtight door seal and brass threshold transition plate under the door.",
            )
        return VastuRemedyKit(
            furniture_remedy="Arrange heavy storage cabinets against the South and West walls; leave North and East sides open.",
            color_therapy="Use reflective light pastel tones to amplify ambient illumination and visual openness.",
            elemental_cure="Place a fresh indoor peace lily or snake plant in a ceramic pot near the entryway.",
            energy_neutralizer="Hang a gentle 5-rod metallic wind chime or install warm 2700K indirect cove lighting.",
        )

    @classmethod
    def _get_interior_tips(cls, room_type: str, zone: str) -> list[str]:
        """Provides bulleted interior arrangement tips for architects and homeowners."""
        if room_type == "kitchen":
            return [
                "🔥 Gas burner / induction hob: Place in South-East corner of the counter.",
                "💧 Kitchen sink & water purifier: Locate in North-East corner of the counter to maintain fire-water separation.",
                "🧊 Refrigerator: Position in South-West or North-West corner, leaving 2 inches clearance from the wall.",
                "🍞 Microwave & electrical appliances: Best installed on the South-East counter ledge.",
            ]
        if room_type in ("master", "bedroom"):
            return [
                "🛏️ Bed positioning: Head towards South (best for cardiovascular rest) or East (best for students/mental focus).",
                "🪞 Mirrors & Dressing Table: Place on North or East wall so you face North/East while grooming; never directly reflect bed.",
                "🚪 Wardrobes & Heavy Storage: Build against South and West perimeter walls.",
                "📺 Electronics & TV: If present, place in South-East corner of the room; turn off completely during sleep.",
            ]
        if room_type == "living":
            return [
                "🛋️ Sofa & Primary Seating: Position against South and West walls, facing North or East.",
                "🖼️ Artwork & Wall Decor: Hang scenic nature, mountain, or landscape artwork on South/West walls; water features on North/East.",
                "🪴 Plants & Flora: Keep light indoor plants in North-East and North zones.",
                "💡 Lighting: Maximize natural dawn lighting from North and East windows; use warm ceiling chandeliers in center.",
            ]
        return [
            "Keep the center of the room clutter-free for free energy movement.",
            "Maintain higher sill-level openings on South/West and lower, wider windows on North/East.",
            "Use natural materials like teak wood, cotton, and linen for upholstery.",
        ]

    @classmethod
    def _audit_entrances(cls, building: BuildingModel, length: float, width: float) -> dict[str, Any]:
        """Audits the main entrance door or gate for cardinal Vastu pada alignment."""
        gates = getattr(building, "main_gates", [])
        doors = getattr(building, "doors", [])

        # Check primary gate if available, otherwise check first exterior door
        target_obj = gates[0] if gates else (doors[0] if doors else None)
        if not target_obj:
            return {
                "status": "Not Specified",
                "score": 85,
                "zone": "North / East Expected",
                "verdict": "Main gate not explicitly modeled; defaulting to North/East standard architectural assumptions.",
            }

        gx_norm = float(target_obj.x) / length
        gy_norm = float(target_obj.y) / width

        # Cardinal boundary check
        if gy_norm >= 0.85:
            direction = "North"
            auspicious = True
            pad_name = "Mukhya / Bhallata (High Prosperity & Career)"
            score = 95
            dosha = None
            remedy = "Auspicious North entrance. Keep entrance well-lit with white light and adorn with an elegant nameplate."
        elif gx_norm >= 0.85:
            direction = "East"
            auspicious = True
            pad_name = "Jayanta / Indra (Vitality & Social Success)"
            score = 95
            dosha = None
            remedy = "Highly auspicious East entrance. Welcome morning sun prana; maintain clean threshold free of footwear clutter."
        elif gx_norm <= 0.15 and gy_norm <= 0.25:
            direction = "South-West"
            auspicious = False
            pad_name = "Nairutya / Rahu (Turbulence Zone)"
            score = 50
            dosha = "South-West entrance can allow instability and fluctuating financial reserves."
            remedy = "Affix a lead or brass pyramid strip beneath the doorway threshold; place a yellow jasper stone or Swastik brass emblem above frame."
        elif gy_norm <= 0.15:
            direction = "South"
            auspicious = False
            pad_name = "Dakshina / Yama (Requires Protection)"
            score = 65
            dosha = "South facing entrance needs grounding to balance solar-heat ingress."
            remedy = "Use a heavy solid teakwood double door; place a copper Swastik symbol above lintel; paint entrance in warm cream or desert sand."
        elif gx_norm <= 0.15:
            direction = "West"
            auspicious = True
            pad_name = "Pushpadanta / Varuna (Financial Gains)"
            score = 80
            dosha = None
            remedy = "Auspicious West entrance. Install brass fittings on door and ensure clean white or cream foyer lighting."
        else:
            direction = "North-West"
            auspicious = True
            pad_name = "Vayavya (Dynamic Motion)"
            score = 75
            dosha = None
            remedy = "Air-zone entrance. Install a gentle metal wind chime to harmonize kinetic energy."

        return {
            "direction": direction,
            "auspicious": auspicious,
            "pad_name": pad_name,
            "score": score,
            "zone": f"{direction} Gateway",
            "dosha": dosha,
            "remedy": remedy,
        }

    @classmethod
    def _generate_key_recommendations(
        cls,
        room_audits: list[VastuRoomAudit],
        central_pillars: list[Any],
        entrance_audit: dict[str, Any],
    ) -> list[str]:
        """Produces prioritized high-impact recommendations for customer review."""
        recs: list[str] = []

        kitchens = [a for a in room_audits if "kitchen" in a.room_name.lower()]
        if any(a.score < 80 for a in kitchens):
            recs.append("🔥 Kitchen Alignment: Orient cooktop so the chef faces East while preparing meals to channel Agni (solar) digestive vitality.")
        else:
            recs.append("🔥 Kitchen Fire Balance: Ensure microwave/ovens are consolidated in the South-East quadrant, keeping clear distance from water sinks.")

        masters = [a for a in room_audits if "master" in a.room_name.lower()]
        if any(a.score < 80 for a in masters):
            recs.append("👑 Master Suite Harmony: Position master bedhead toward South or East to ground blood circulation with Earth's geomagnetic flux.")
        else:
            recs.append("👑 Master Suite Excellence: South-West master bedroom verified; anchor the space with heavy wooden furniture on South and West walls.")

        if central_pillars:
            recs.append(f"🏛️ Brahmasthan Core: {len(central_pillars)} central structural pillar(s) detected. Paint pillars warm ivory and illuminate with uplighting to neutralize visual heaviness.")
        else:
            recs.append("🏛️ Brahmasthan Core: The central space is open and unencumbered — an auspicious conduit for cosmic light and natural airflow.")

        recs.append("💧 North-East (Ishanya): Maintain this quadrant light, clean, and install an indoor water feature, meditation corner, or indoor plant.")

        if entrance_audit.get("dosha"):
            recs.append(f"🚪 Entrance Remedy: {entrance_audit['dosha']} — {entrance_audit['remedy']}")

        return recs

    @classmethod
    def _generate_actionable_checklist(
        cls,
        room_audits: list[VastuRoomAudit],
        central_pillars: list[Any],
        entrance_audit: dict[str, Any],
    ) -> list[str]:
        """Provides a punchy 10-point actionable checklist for builders and buyers."""
        checklist = [
            "✅ Sleep with head towards South or East for optimal cardiovascular rest and restorative sleep.",
            "✅ Face East while cooking to harness natural morning solar prana.",
            "✅ Keep the North-East (Ishanya) quadrant clean, light, and free from heavy storage or clutter.",
            "✅ Position heavy wardrobes, safes, and solid storage along the South and West perimeter walls.",
            "✅ Avoid placing mirrors directly opposite any sleeping bed; mount mirrors on North or East walls.",
            "✅ Maintain toilet doors permanently closed and ensure proper mechanical exhaust ventilation.",
            "✅ Ensure water taps, purifiers, and underground sumps are positioned in the North or North-East.",
            "✅ Place overhead water storage tanks in the highest, heaviest corner: the South-West.",
            "✅ Ascend staircases in a clockwise (Pradakshina) direction starting from North/East towards South/West.",
            "✅ Illuminate the main foyer with warm 3000K lighting and avoid shoe-rack clutter near the main door.",
        ]
        return checklist

    @classmethod
    def _generate_executive_summary(
        cls,
        overall_score: int,
        grade: str,
        room_audits: list[VastuRoomAudit],
        doshas: list[dict[str, str]],
    ) -> str:
        """Generates an elegant, professional narrative suitable for client presentations."""
        ideal_count = sum(1 for a in room_audits if a.compliance == "Ideal")
        fav_count = sum(1 for a in room_audits if a.compliance == "Favorable")
        total_rooms = len(room_audits)

        if overall_score >= 85:
            sentiment = "exhibits an exceptional degree of directional alignment, creating a profoundly balanced living environment that fosters peace, vitality, and sustained prosperity."
        elif overall_score >= 70:
            sentiment = "demonstrates sound architectural harmony, with key functional zones properly oriented. A few minor interior cures will easily elevate the property to peak spatial resonance."
        else:
            sentiment = "presents opportunities for targeted spatial harmonization. Through non-destructive architectural remedies (color therapy, layout adjustments, and elemental placement), full balance can be achieved without structural changes."

        summary = (
            f"BuildMetrics AI Vastu Analysis: This layout achieves an overall Spatial Harmony score of "
            f"**{overall_score}/100 ({grade})**. Out of {total_rooms} audited rooms, **{ideal_count + fav_count} ({((ideal_count + fav_count)/max(1, total_rooms)):.0%})** "
            f"are positioned in auspicious sectors. The building {sentiment} "
            f"There are {len(doshas)} identified spatial point(s) requiring non-invasive remedial attention, all of which "
            f"can be completely harmonized through strategic furniture arrangement, element balancing, and color therapy."
        )
        return summary

    @classmethod
    def _get_scientific_foundations(cls) -> list[dict[str, str]]:
        """Educational primer explaining why Vastu Shastra is modern bio-climatic architecture."""
        return [
            {
                "title": "☀️ Solar Path & Photobiology",
                "subtitle": "Circadian Rhythm & Vitamin D Synthesis",
                "explanation": (
                    "Earth's rotation brings early morning sunrise in the East. Dawn sunlight contains beneficial "
                    "UV-A rays that destroy nocturnal pathogens and stimulate human serotonin/melatonin regulation. "
                    "Vastu mandates morning rooms (Pooja, Living, Study) in the East/North-East to harvest this healthy light, "
                    "while shifting bedrooms and storage to the South-West where late-afternoon harsh infrared heat is buffered."
                ),
            },
            {
                "title": "🧲 Geomagnetic Flux Alignment",
                "subtitle": "Magnetic Dip & Cardiovascular Blood Flow",
                "explanation": (
                    "Earth acts as a massive dipole magnet with magnetic flux streaming from South to North. The human body "
                    "also possesses a biomagnetic field (head is positive/North pole, feet negative/South pole). Sleeping with "
                    "head to South creates magnetic attraction ('opposites attract'), ensuring smooth hemodynamics and iron-ion "
                    "distribution in hemoglobin, resulting in deep non-REM restorative sleep."
                ),
            },
            {
                "title": "💨 Prevailing Winds & Passive Cooling",
                "subtitle": "Coriolis Chimney Effect & Natural Aeration",
                "explanation": (
                    "The Brahmasthan (central core) serves as a thermal chimney. When left open and lightweight, warm air naturally "
                    "rises and exhausts through high louvers, pulling cool, fresh breezes in through lower North and East windows. "
                    "This creates continuous passive cross-ventilation, slashing HVAC energy demand and mold proliferation."
                ),
            },
            {
                "title": "🧱 Five Elements (Pancha Bhoota) Equilibrium",
                "subtitle": "Environmental Psychology & Biophilia",
                "explanation": (
                    "The human brain seeks elemental coherence. Aligning Water (calmness) in North-East, Fire (metabolism) in South-East, "
                    "Earth (anchoring stability) in South-West, Air (social movement) in North-West, and Space (openness) in the center "
                    "satisfies evolutionary biophilic design principles, reducing cortisol levels and cognitive fatigue."
                ),
            },
        ]

    # Backward compatibility alias
    evaluate_layout = audit_building

