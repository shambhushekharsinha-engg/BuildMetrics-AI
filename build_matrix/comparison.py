"""
BuildMetrics AI — Blueprint Comparison Utility
Computes structured diffs between two BuildingModel instances.
Used in the AI chat diff view and the new "Compare Designs" feature.
"""
from dataclasses import dataclass
from typing import Optional

from build_matrix.models import BuildingModel


@dataclass
class DesignDiff:
    """Structured comparison between two building designs."""
    
    # Cost changes
    cost_usd_before: float
    cost_usd_after: float
    cost_delta_usd: float
    cost_pct_change: float
    
    # Area changes  
    area_m2_before: float
    area_m2_after: float
    area_delta_m2: float
    
    # Structural element counts
    rooms_before: int
    rooms_after: int
    pillars_before: int
    pillars_after: int
    floors_before: int
    floors_after: int
    
    # Compliance
    violations_before: int
    violations_after: int
    
    # Timeline
    days_before: int
    days_after: int
    
    # Room-level changes
    added_rooms: list[str]
    removed_rooms: list[str]
    resized_rooms: list[str]
    
    @property
    def cost_direction(self) -> str:
        if self.cost_delta_usd > 500:
            return "increased"
        elif self.cost_delta_usd < -500:
            return "decreased"
        return "unchanged"

    @property
    def summary_emoji(self) -> str:
        """Quick visual health indicator for the diff."""
        if self.violations_after > self.violations_before:
            return "⚠️"
        elif self.cost_delta_usd > 0 and self.area_delta_m2 > 0:
            return "📈"
        elif self.cost_delta_usd < 0:
            return "💰"
        return "🔄"

    def to_markdown(self) -> str:
        """Render the diff as a Markdown summary for the chat history."""
        lines = []
        lines.append(f"**{self.summary_emoji} Design Comparison**\n")
        
        # Cost
        cost_sign = "+" if self.cost_delta_usd >= 0 else ""
        cost_pct_sign = "+" if self.cost_pct_change >= 0 else ""
        lines.append(f"**💰 Cost:** ${self.cost_usd_before:,.0f} → ${self.cost_usd_after:,.0f} "
                     f"({cost_sign}${abs(self.cost_delta_usd):,.0f} / {cost_pct_sign}{self.cost_pct_change:.1f}%)")
        
        # Area
        area_sign = "+" if self.area_delta_m2 >= 0 else ""
        lines.append(f"**📐 Built Area:** {self.area_m2_before:.0f} m² → {self.area_m2_after:.0f} m² "
                     f"({area_sign}{self.area_delta_m2:.0f} m²)")
        
        # Timeline
        day_diff = self.days_after - self.days_before
        day_sign = "+" if day_diff >= 0 else ""
        lines.append(f"**⏱️ Timeline:** {self.days_before} → {self.days_after} days ({day_sign}{day_diff})")
        
        # Compliance
        if self.violations_after > self.violations_before:
            lines.append(f"**⚠️ Compliance:** {self.violations_before} → {self.violations_after} violations (new issues introduced)")
        elif self.violations_after < self.violations_before:
            lines.append(f"**✅ Compliance:** {self.violations_before} → {self.violations_after} violations (improved)")
        else:
            lines.append(f"**✅ Compliance:** unchanged ({self.violations_after} violations)")
        
        # Room changes
        if self.added_rooms:
            lines.append(f"**➕ Added:** {', '.join(self.added_rooms)}")
        if self.removed_rooms:
            lines.append(f"**➖ Removed:** {', '.join(self.removed_rooms)}")
        if self.resized_rooms:
            lines.append(f"**↔️ Resized:** {', '.join(self.resized_rooms)}")
        if not (self.added_rooms or self.removed_rooms or self.resized_rooms):
            lines.append("**Rooms:** No structural room changes")
        
        return "\n".join(lines)


def compare_designs(before: BuildingModel, after: BuildingModel) -> DesignDiff:
    """
    Compute a structured diff between two building models.
    
    Args:
        before: The original BuildingModel.
        after: The updated BuildingModel.
    
    Returns:
        A DesignDiff with all computed change metrics.
    """
    # Cost
    cost_before = before.boq_estimate.cost_usd if before.boq_estimate else 0.0
    cost_after = after.boq_estimate.cost_usd if after.boq_estimate else 0.0
    cost_delta = cost_after - cost_before
    cost_pct = ((cost_after - cost_before) / max(cost_before, 1)) * 100
    
    # Area
    area_before = sum(before.total_building_area(f) for f in range(1, before.plot.num_floors + 1))
    area_after = sum(after.total_building_area(f) for f in range(1, after.plot.num_floors + 1))
    
    # Compliance
    viol_before = sum(1 for a in before.annotations 
                      if a.category == 'compliance_tag' and a.style_props.get('color') == 'red')
    viol_after = sum(1 for a in after.annotations 
                     if a.category == 'compliance_tag' and a.style_props.get('color') == 'red')
    
    # Timeline
    days_before = 90 + (before.plot.num_floors * 45)
    days_before = days_before + int(days_before * 0.12)
    days_after = 90 + (after.plot.num_floors * 45)
    days_after = days_after + int(days_after * 0.12)
    
    # Room-level diff
    rooms_before_map = {(r.room_type.lower(), r.floor): r for r in before.rooms}
    rooms_after_map = {(r.room_type.lower(), r.floor): r for r in after.rooms}
    
    before_keys = set(rooms_before_map.keys())
    after_keys = set(rooms_after_map.keys())
    
    added = [f"{k[0].title()} (F{k[1]})" for k in after_keys - before_keys]
    removed = [f"{k[0].title()} (F{k[1]})" for k in before_keys - after_keys]
    resized = []
    for k in before_keys & after_keys:
        area_b = rooms_before_map[k].area
        area_a = rooms_after_map[k].area
        if abs(area_a - area_b) > 0.5:
            resized.append(f"{k[0].title()} F{k[1]}: {area_b:.1f}→{area_a:.1f} m²")
    
    return DesignDiff(
        cost_usd_before=cost_before,
        cost_usd_after=cost_after,
        cost_delta_usd=cost_delta,
        cost_pct_change=cost_pct,
        area_m2_before=area_before,
        area_m2_after=area_after,
        area_delta_m2=area_after - area_before,
        rooms_before=len(before.rooms),
        rooms_after=len(after.rooms),
        pillars_before=len(before.pillars),
        pillars_after=len(after.pillars),
        floors_before=before.plot.num_floors,
        floors_after=after.plot.num_floors,
        violations_before=viol_before,
        violations_after=viol_after,
        days_before=days_before,
        days_after=days_after,
        added_rooms=added,
        removed_rooms=removed,
        resized_rooms=resized,
    )
