def calculate_concrete_volume(area_sqft, floors, thickness_ft=0.5):
    area_sqm = area_sqft * 0.092903
    thickness_m = thickness_ft * 0.3048
    v_cum = area_sqm * thickness_m * floors
    return v_cum

def calculate_steel_weight(v_cum):
    return v_cum * 0.015 * 7850

def calculate_brickwork(perimeter_ft, height_ft, floors, factor=50):
    perimeter_m = perimeter_ft * 0.3048
    height_m = height_ft * 0.3048
    wall_area_sqm = perimeter_m * height_m * floors
    return wall_area_sqm * factor

def calculate_dry_mortar(wet_volume_cum):
    return wet_volume_cum * 1.54

def calculate_labor_and_time(area_sqft, floors):
    # Rough estimate: 1 skilled + 2 unskilled labor can build 100 sqft per day
    total_sqft = area_sqft * floors
    estimated_days = total_sqft / 100
    labor_mandays = estimated_days * 3 # 3 laborers per 100 sqft block
    return {
        'estimated_days': int(estimated_days),
        'total_mandays': int(labor_mandays)
    }

def calculate_quantities(area_sqft, perimeter_ft, floors):
    if perimeter_ft is None:
        side = area_sqft ** 0.5
        perimeter_ft = 4 * side
        
    v_cum = calculate_concrete_volume(area_sqft, floors)
    steel_kg = calculate_steel_weight(v_cum)
    bricks = calculate_brickwork(perimeter_ft, 10, floors) 
    
    brick_volume_cum = bricks * 0.002
    wet_mortar_cum = brick_volume_cum * 0.30
    dry_mortar_cum = calculate_dry_mortar(wet_mortar_cum)
    
    labor_stats = calculate_labor_and_time(area_sqft, floors)
    
    return {
        'concrete_cum': round(v_cum, 2),
        'steel_kg': round(steel_kg, 2),
        'bricks': int(bricks),
        'dry_mortar_cum': round(dry_mortar_cum, 2),
        'estimated_days': labor_stats['estimated_days'],
        'total_mandays': labor_stats['total_mandays']
    }
