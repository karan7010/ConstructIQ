def calculate_materials(geometry: dict) -> dict:
    total_wall_area = geometry.get("totalWallArea", 0.0)        # m2
    total_floor_area = geometry.get("totalFloorArea", 0.0)      # m2
    structural_volume = geometry.get("structuralVolume", 0.0)   # m3

    # Brick masonry (standard brick, 1:6 mortar)
    total_bricks = total_wall_area * 50                # 50 bricks per m2 of wall

    # Cement for masonry
    cement_bags_masonry = total_wall_area * 0.3        # 0.3 bags per m2

    # RCC slab (M20 grade, 150mm thickness)
    concrete_volume = total_floor_area * 0.15
    cement_bags_concrete = concrete_volume * 8         # 8 bags per m3 for M20
    sand_m3 = concrete_volume * 0.42
    aggregate_m3 = concrete_volume * 0.84

    # Steel reinforcement (1% ratio, density 7850 kg/m3)
    steel_kg = structural_volume * 78.5

    # Totals
    total_cement_bags = cement_bags_masonry + cement_bags_concrete

    return {
        "cement": {"quantity": round(total_cement_bags, 1), "unit": "bags"},
        "bricks": {"quantity": int(total_bricks), "unit": "nos"},
        "steel": {"quantity": round(steel_kg, 1), "unit": "kg"},
        "sand": {"quantity": round(sand_m3, 2), "unit": "m3"},
        "aggregate": {"quantity": round(aggregate_m3, 2), "unit": "m3"}
    }

def calculate_labour(materials: dict, geometry: dict) -> dict:
    total_bricks    = materials.get("bricks", {}).get("quantity", 0)
    concrete_volume = geometry.get("totalFloorArea", 0.0) * 0.15
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
            "norm": "1.5 m³ concrete/labourer/day",
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
