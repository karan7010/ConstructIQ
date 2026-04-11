"""
Estimation engine for ConstructIQ.
Uses CPWD (Central Public Works Department) standard formulas for construction materials.
"""

def calculate_materials(geometry: dict) -> dict:
    """
    Takes geometry breakdown and returns material quantities
    based on CPWD standard estimation formulas (QTO).
    """
    # ── INPUTS (Metres and Metres Squared/Cubed)
    wall_area       = geometry.get("totalWallArea", 0.0)      # m²
    floor_area      = geometry.get("totalFloorArea", 0.0)     # m²
    height          = geometry.get("buildingHeight", 3.0)     # m
    beam_length     = geometry.get("beamLength", 0.0)         # m
    col_count       = geometry.get("totalColumnCount", 0)     # nos
    stair_area      = geometry.get("stairArea", 0.0)          # m²
    door_count      = geometry.get("doorCount", 0)            # nos
    window_count    = geometry.get("windowCount", 0)          # nos

    # ── DEDUCTIONS (Net Wall Area)
    # Average door 2.1m x 1m, average window 1.5m x 1.2m
    deductions      = (door_count * 2.1) + (window_count * 1.8)
    net_wall_area   = max(0.0, wall_area - deductions)

    # 1. BRICK MASONRY (230mm wall thickness)
    # Formula: 1m³ of masonry needs 500 bricks + 0.25m³ mortar
    # 230mm wall = 0.23m³ volume per 1m² of surface
    masonry_vol     = net_wall_area * 0.23
    total_bricks    = masonry_vol * 500
    cement_masonry  = masonry_vol * 1.2         # bags (approx 1:6 ratio)
    sand_masonry    = masonry_vol * 0.22        # m³

    # 2. RCC SLAB (M25 Grade, 150mm thick)
    # Formula: 1m³ needs 8.4 bags cement, 0.45m³ sand, 0.90m³ aggregate
    slab_vol        = (floor_area + stair_area) * 0.15
    cement_slab     = slab_vol * 8.4
    sand_slab       = slab_vol * 0.45
    aggregate_slab  = slab_vol * 0.90

    # 3. BEAMS & COLUMNS (Structural reinforcement)
    # Assumed cross-sections for estimation: Beam 0.3x0.45, Column 0.3x0.3
    beam_vol        = beam_length * (0.3 * 0.45)
    col_vol         = col_count * (0.3 * 0.3 * height)
    cement_beam     = beam_vol * 8.4
    cement_col      = col_vol * 8.4
    aggregate_beam  = beam_vol * 0.90
    aggregate_col   = col_vol * 0.90

    # 4. STEEL (General 1.2% reinforcement by volume)
    # Density of steel = 7850 kg/m³
    total_rcc_vol   = slab_vol + beam_vol + col_vol
    total_steel     = total_rcc_vol * (0.012 * 7850)

    # 5. STAIRCASE (Concrete + Steps)
    stair_vol       = stair_area * 0.25  # Average waist + steps thickness
    cement_stair    = stair_vol * 8.4
    aggregate_stair = stair_vol * 0.90

    # 6. PLASTERING (both faces of internal walls + one face external)
    # External walls: both faces. Internal walls: both faces.
    # Estimate: 1.8x wall area for plastering (accounts for two faces)
    plaster_area    = net_wall_area * 1.8
    cement_plaster  = plaster_area * 0.11       # 0.11 bags/m² for 12mm plaster
    sand_plaster    = plaster_area * 0.022      # Corrected from sand_plastering

    # 7. FLOOR SCREED (40mm thickness)
    screed_vol      = floor_area * 0.04
    cement_screed   = screed_vol * 10
    sand_screed     = screed_vol * 0.04

    # ── TOTALS
    total_cement    = (cement_masonry + cement_slab + cement_stair +
                       cement_beam + cement_col + cement_plaster + cement_screed)
    total_sand      = sand_masonry + sand_slab + sand_plaster + sand_screed
    total_aggregate = aggregate_slab + aggregate_stair + aggregate_beam + aggregate_col

    return {
        "cement":    {"quantity": round(total_cement, 1), "unit": "bags"},
        "bricks":    {"quantity": int(total_bricks), "unit": "nos"},
        "steel":     {"quantity": round(total_steel, 1), "unit": "kg"},
        "sand":      {"quantity": round(total_sand, 2), "unit": "m³"},
        "aggregate": {"quantity": round(total_aggregate, 2), "unit": "m³"},
        "metadata": {
            "net_wall_area": round(net_wall_area, 2),
            "masonry_vol": round(masonry_vol, 2),
            "rcc_vol": round(total_rcc_vol, 2),
            "plaster_area": round(plaster_area, 2)
        }
    }


def calculate_labour(materials: dict, geometry: dict) -> dict:
    """Calculates trade-wise labour days based on CPWD productivity norms."""
    total_bricks    = materials.get("bricks", {}).get("quantity", 0)
    concrete_volume = (geometry.get("totalFloorArea", 0.0) * 0.15 + 
                       geometry.get("beamLength", 0.0) * 0.135)
    steel_kg        = materials.get("steel", {}).get("quantity", 0.0)
    total_wall_area = geometry.get("totalWallArea", 0.0)

    return {
        "brick_masonry": {
            "labour_days": round(total_bricks / 400) if total_bricks else 0,
            "trade": "Mason",
            "norm": "400 bricks/mason/day",
            "norm_source": "CPWD"
        },
        "rcc_concrete": {
            "labour_days": round(concrete_volume / 1.5) if concrete_volume else 0,
            "trade": "Labourer",
            "norm": "1.5 m³ concrete/labour/day",
            "norm_source": "CPWD"
        },
        "steel_fixing": {
            "labour_days": round(steel_kg / 200) if steel_kg else 0,
            "trade": "Steel fixer",
            "norm": "200 kg steel/fixer/day",
            "norm_source": "CPWD"
        },
        "plastering": {
            "labour_days": round(total_wall_area / 11) if total_wall_area else 0,
            "trade": "Plasterer",
            "norm": "11 m² wall/plasterer/day",
            "norm_source": "CPWD"
        }
    }
