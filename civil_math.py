def calculate_concrete_volume(area_sqft, floors, thickness_ft=0.5):
    # Convert area and thickness to meters if needed, but let's assume V = Area * Thickness * Floors
    # Let's keep it in the same units or convert to metric since steel density is kg/m^3
    # 1 sq ft = 0.092903 sq m
    # 1 ft = 0.3048 m
    area_sqm = area_sqft * 0.092903
    thickness_m = thickness_ft * 0.3048
    v_cum = area_sqm * thickness_m * floors
    return v_cum

def calculate_steel_weight(v_cum):
    # W = V * 1.5% * 7850 kg/m^3
    return v_cum * 0.015 * 7850

def calculate_brickwork(perimeter_ft, height_ft, floors, factor=50):
    # Perimeter * Height * Factor
    # Using a standard factor like 50 bricks per sq meter, but let's use the inputs.
    # Convert perimeter and height to meters to apply standard metric factor if desired, or keep as is.
    perimeter_m = perimeter_ft * 0.3048
    height_m = height_ft * 0.3048
    wall_area_sqm = perimeter_m * height_m * floors
    bricks = wall_area_sqm * factor
    return bricks

def calculate_dry_mortar(wet_volume_cum):
    # Dry volume = Wet volume * 1.54
    return wet_volume_cum * 1.54

def calculate_quantities(area_sqft, perimeter_ft, floors):
    v_cum = calculate_concrete_volume(area_sqft, floors)
    steel_kg = calculate_steel_weight(v_cum)
    bricks = calculate_brickwork(perimeter_ft, 10, floors) # assuming 10ft height per floor
    
    # Assume wet mortar volume is around 0.002 cum per brick (typical mortar volume per brick including wastage)
    wet_mortar_cum = bricks * 0.002 * 0.25 # just an approximation
    dry_mortar_cum = calculate_dry_mortar(wet_mortar_cum)
    
    return {
        'concrete_cum': round(v_cum, 2),
        'steel_kg': round(steel_kg, 2),
        'bricks': int(bricks),
        'dry_mortar_cum': round(dry_mortar_cum, 2)
    }
