"""
BuildMetrics AI — Vastu Shastra & Spatial Harmony Orientation Engine
Performs geometric directional zone audits (9-sector Vastu Purusha Mandala)
evaluating room allocations, element balance (Pancha Bhoota), and architectural remedies.
"""

from dataclasses import dataclass

from build_matrix.models import BuildingModel


@dataclass
class VastuRoomAudit:
    room_id: str
    room_name: str
    zone: str               # NE, N, NW, E, Brahmasthan, W, SE, S, SW
    ideal_zones: list[str]
    compliance: str         # "Ideal", "Favorable", "Neutral", "Non-Compliant"
    score: int              # 0 to 100
    remedy: str             # Remedial architectural action or interior tip


@dataclass
class VastuReport:
    overall_score: int              # 0 to 100
    grade: str                      # A+ Auspicious, A Harmonious, B Balanced, C Needs Remedies
    brahmasthan_status: str         # "Clear & Auspicious" or "Obstructed"
    element_scores: dict[str, int]  # Water, Fire, Earth, Air, Space (0-100)
    room_audits: list[VastuRoomAudit]
    key_recommendations: list[str]


class VastuEngine:
    """Evaluates 9-zone directional harmony according to traditional Vastu Shastra."""

    ZONES = {
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

    IDEAL_ALLOCATIONS: dict[str, list[str]] = {
        "living": ["North-East (Ishanya)", "North (Uttara)", "East (Purva)"],
        "master": ["South-West (Nairutya)", "South (Dakshina)", "West (Paschim)"],
        "bedroom": ["South-West (Nairutya)", "South (Dakshina)", "West (Paschim)", "North-West (Vayavya)"],
        "kitchen": ["South-East (Agni)", "North-West (Vayavya)"],
        "study": ["North-East (Ishanya)", "North (Uttara)", "East (Purva)"],
        "pooja": ["North-East (Ishanya)", "North (Uttara)", "East (Purva)"],
        "dining": ["West (Paschim)", "East (Purva)", "North (Uttara)"],
        "staircase": ["South (Dakshina)", "West (Paschim)", "South-West (Nairutya)"],
        "bathroom": ["North-West (Vayavya)", "West (Paschim)", "South (Dakshina)"],
        "balcony": ["North-East (Ishanya)", "North (Uttara)", "East (Purva)"],
    }

    @classmethod
    def audit_building(cls, building: BuildingModel) -> VastuReport:
        plot = building.plot
        length, width = plot.length, plot.width
        room_audits: list[VastuRoomAudit] = []

        total_score = 0
        scored_rooms = 0

        # Element balance tracking
        element_hits = {"Water (Jal)": 0, "Fire (Agni)": 0, "Earth (Prithvi)": 0, "Air (Vayu)": 0, "Space (Akash)": 0}
        element_totals = {"Water (Jal)": 1, "Fire (Agni)": 1, "Earth (Prithvi)": 1, "Air (Vayu)": 1, "Space (Akash)": 1}

        for r in building.rooms:
            # Normalized coordinates (0 to 1)
            cx = (r.x + r.width / 2.0) / max(length, 1.0)
            cy = (r.y + r.height / 2.0) / max(width, 1.0)

            # Map to 3x3 grid (0, 1, 2)
            gx = min(2, max(0, int(cx * 3)))
            gy = min(2, max(0, int(cy * 3)))
            zone = cls.ZONES.get((gx, gy), "Brahmasthan (Center)")

            # Classify room
            r_type = r.room_type.lower()
            key_match = None
            for k in cls.IDEAL_ALLOCATIONS:
                if k in r_type or k in r.name.lower():
                    key_match = k
                    break
            if not key_match:
                key_match = "bedroom" if "bed" in r_type else "living"

            ideal = cls.IDEAL_ALLOCATIONS.get(key_match, ["North (Uttara)"])

            if zone == ideal[0]:
                compliance = "Ideal"
                score = 100
                remedy = "Optimal location. Maximizes positive directional energy flow."
            elif zone in ideal:
                compliance = "Favorable"
                score = 80
                remedy = "Harmonious placement. Maintain light interior palette and clutter-free entry."
            elif zone == "Brahmasthan (Center)":
                compliance = "Neutral"
                score = 65
                remedy = "Keep room central zone open and ensure adequate overhead natural lighting."
            else:
                compliance = "Non-Compliant"
                score = 40
                remedy = cls._get_remedy(key_match, zone)

            # Element associations
            if "Ishanya" in zone or "Water" in zone:
                element_totals["Water (Jal)"] += 1
                if score >= 80: element_hits["Water (Jal)"] += 1
            if "Agni" in zone or "Fire" in zone:
                element_totals["Fire (Agni)"] += 1
                if score >= 80: element_hits["Fire (Agni)"] += 1
            if "Nairutya" in zone or "Earth" in zone:
                element_totals["Earth (Prithvi)"] += 1
                if score >= 80: element_hits["Earth (Prithvi)"] += 1
            if "Vayavya" in zone or "Air" in zone:
                element_totals["Air (Vayu)"] += 1
                if score >= 80: element_hits["Air (Vayu)"] += 1

            total_score += score
            scored_rooms += 1

            room_audits.append(VastuRoomAudit(
                room_id=r.id,
                room_name=r.name,
                zone=zone,
                ideal_zones=ideal,
                compliance=compliance,
                score=score,
                remedy=remedy,
            ))

        # Check Brahmasthan (Center 20% of plot)
        center_x_min, center_x_max = length * 0.4, length * 0.6
        center_y_min, center_y_max = width * 0.4, width * 0.6
        central_pillars = [
            p for p in building.pillars
            if center_x_min <= p.x <= center_x_max and center_y_min <= p.y <= center_y_max
        ]
        if central_pillars:
            brahmasthan_status = f"Encumbered by {len(central_pillars)} central structural column(s)"
            brahmasthan_score = 60
        else:
            brahmasthan_status = "Clear & Open (Auspicious Energy Core)"
            brahmasthan_score = 95
            element_hits["Space (Akash)"] += 1

        overall_score = int((total_score / max(1, scored_rooms)) * 0.85 + (brahmasthan_score * 0.15))

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

        # Key recommendations
        key_recs: list[str] = []
        kitchens = [a for a in room_audits if "kitchen" in a.room_name.lower()]
        if any(a.score < 75 for a in kitchens):
            key_recs.append("🔥 Kitchen Alignment: Orient cooktop to face East to channel Agni (solar) digestive vitality.")
        
        masters = [a for a in room_audits if "master" in a.room_name.lower()]
        if any(a.score < 75 for a in masters):
            key_recs.append("👑 Master Suite: Position bedhead toward South or East for grounded restful sleep.")

        if central_pillars:
            key_recs.append("🏛️ Brahmasthan: Paint central pillars in warm light ivory and illuminate with uplighting to neutralize visual heaviness.")

        key_recs.append("💧 North-East (Ishanya): Maintain this quadrant light, clean, and install an indoor water feature or indoor plant.")

        return VastuReport(
            overall_score=overall_score,
            grade=grade,
            brahmasthan_status=brahmasthan_status,
            element_scores=element_scores,
            room_audits=room_audits,
            key_recommendations=key_recs,
        )

    @classmethod
    def _get_remedy(cls, room_type: str, zone: str) -> str:
        if room_type == "kitchen":
            return "Place gas burner / cooktop in SE corner of room; utilize warm pastel or cream wall tiles to balance fire energy."
        if room_type in ("master", "bedroom"):
            return "Sleep with head positioned toward South; incorporate earthy tones (terracotta, sandstone) to ground the space."
        if room_type == "living":
            return "Hang a silver bell or crystal chime near the entrance; maximize window ventilation toward North/East."
        return "Keep the space well-ventilated, uncluttered, and illuminated with warm 3000K daylight lighting."
