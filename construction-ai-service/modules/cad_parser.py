"""
Production-grade DXF parser for ConstructIQ.
Handles real architectural floor plans with complex geometry.
Outputs per-element breakdown suitable for detailed material estimation.
"""
import math
import re
import ezdxf
import httpx
import tempfile
import os
from typing import Optional
from collections import defaultdict

# Layer name patterns for automatic identification
WALL_PATTERNS   = ["wall", "walls", "a-wall", "arch-wall", "wl", "partition",
                   "cloison", "mur", "w-", "ext_wall", "int_wall", "bearing"]
FLOOR_PATTERNS  = ["floor", "slab", "dalle", "a-flor", "flr", "ground",
                   "a-slab", "concrete", "rcc", "deck"]
COLUMN_PATTERNS = ["column", "col", "pillar", "struct", "s-col", "a-col",
                   "support", "pier", "post"]
DOOR_PATTERNS   = ["door", "a-door", "dr", "porte"]
WINDOW_PATTERNS = ["window", "win", "a-glaz", "fenetre"]
BEAM_PATTERNS   = ["beam", "girder", "joist", "lintel"]
STAIR_PATTERNS  = ["stair", "step", "ramp", "escalier"]
DIM_PATTERNS    = ["dim", "dimension", "anno", "annotation", "text", "a-anno",
                   "note", "label"]


def _layer_matches(layer_name: str, patterns: list) -> bool:
    name = layer_name.lower().strip()
    return any(p in name for p in patterns)


def _shoelace_area(points: list) -> float:
    """Calculate polygon area using shoelace formula."""
    n = len(points)
    if n < 3:
        return 0.0
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += points[i][0] * points[j][1]
        area -= points[j][0] * points[i][1]
    return abs(area / 2.0)


def _arc_length(entity) -> float:
    try:
        radius = entity.dxf.radius
        start = math.radians(entity.dxf.start_angle)
        end = math.radians(entity.dxf.end_angle)
        if end < start:
            end += 2 * math.pi
        return radius * (end - start)
    except Exception:
        return 0.0


def _spline_length(entity) -> float:
    try:
        points = list(entity.flattening(0.01))
        total = 0.0
        for i in range(len(points) - 1):
            dx = points[i + 1][0] - points[i][0]
            dy = points[i + 1][1] - points[i][1]
            total += math.sqrt(dx * dx + dy * dy)
        return total
    except Exception:
        return 0.0


def _polyline_length_and_area(entity):
    """Returns (length, area) for LWPOLYLINE."""
    try:
        pts = [(p[0], p[1]) for p in entity.get_points()]
        length = 0.0
        for i in range(len(pts) - 1):
            dx = pts[i + 1][0] - pts[i][0]
            dy = pts[i + 1][1] - pts[i][1]
            length += math.sqrt(dx * dx + dy * dy)
        if entity.is_closed and len(pts) > 1:
            dx = pts[0][0] - pts[-1][0]
            dy = pts[0][1] - pts[-1][1]
            length += math.sqrt(dx * dx + dy * dy)
        area = _shoelace_area(pts) if entity.is_closed else 0.0
        return length, area
    except Exception:
        return 0.0, 0.0


def _hatch_area(entity) -> float:
    try:
        total = 0.0
        for path in entity.paths:
            path_type = type(path).__name__
            if "PolylinePath" in path_type:
                pts = [(v[0], v[1]) for v in path.vertices]
                total += _shoelace_area(pts)
            elif "EdgePath" in path_type:
                pts = []
                for edge in path.edges:
                    etype = type(edge).__name__
                    if "LineEdge" in etype:
                        pts.append((edge.start[0], edge.start[1]))
                    elif "ArcEdge" in etype:
                        cx, cy = edge.center[0], edge.center[1]
                        r = edge.radius
                        sa = math.radians(edge.start_angle)
                        ea = math.radians(edge.end_angle)
                        if ea < sa:
                            ea += 2 * math.pi
                        for t in range(8):
                            angle = sa + (ea - sa) * t / 8
                            pts.append((cx + r * math.cos(angle),
                                        cy + r * math.sin(angle)))
                    elif "SplineEdge" in etype:
                        if hasattr(edge, 'control_points') and edge.control_points:
                            for cp in edge.control_points:
                                pts.append((cp[0], cp[1]))
                if pts:
                    total += _shoelace_area(pts)
        return total
    except Exception:
        return 0.0


def _extract_height(msp) -> tuple[Optional[float], str]:
    """
    Extract building height from TEXT/MTEXT annotations.
    Returns (height_in_metres, source_description).
    """
    height_pattern = re.compile(
        r'(\d+\.?\d*)\s*["\']?\s*(m|mm|ft|feet|meter|metre|\'|\")',
        re.IGNORECASE
    )
    candidates = []
    for entity in msp.query("TEXT MTEXT"):
        try:
            text = (entity.dxf.text
                    if hasattr(entity.dxf, 'text')
                    else entity.text)
            text = text.strip()
            for val_str, unit in height_pattern.findall(text):
                val = float(val_str)
                if unit.lower() == 'mm':
                    val /= 1000
                elif unit.lower() in ('ft', 'feet', "'"):
                    val *= 0.3048
                if 2.0 <= val <= 20.0:
                    candidates.append(val)
        except Exception:
            continue

    if candidates:
        from collections import Counter
        most_common = Counter(
            [round(v, 1) for v in candidates]
        ).most_common(1)[0][0]
        return most_common, "extracted from drawing annotations"
    return None, "default (3.0m assumed — no height annotation found)"


def _expand_inserts(msp, doc) -> list:
    """Expand INSERT (block reference) entities to get all geometry."""
    extra_entities = []
    try:
        for insert in msp.query("INSERT"):
            block_name = insert.dxf.name
            if block_name in doc.blocks:
                for entity in doc.blocks[block_name]:
                    extra_entities.append((entity, insert.dxf.layer))
    except Exception:
        pass
    return extra_entities


def parse_dxf_file(file_path: str) -> dict:
    """
    Main parsing function. Returns comprehensive geometry breakdown.
    """
    doc = ezdxf.readfile(file_path)
    msp = doc.modelspace()

    # Accumulators
    wall_length_by_layer = defaultdict(float)
    floor_area_by_layer  = defaultdict(float)
    column_count         = 0
    column_area          = 0.0
    door_count           = 0
    window_count         = 0
    beam_length          = 0.0
    stair_area           = 0.0
    hatch_areas_found    = False

    # Process all entities in modelspace
    all_entities = list(msp)
    extra        = _expand_inserts(msp, doc)

    def process_entity(entity, override_layer=None):
        nonlocal column_count, column_area, door_count
        nonlocal window_count, beam_length, stair_area, hatch_areas_found

        try:
            layer = override_layer or getattr(entity.dxf, 'layer', '0')
            etype = entity.dxftype()

            is_wall    = _layer_matches(layer, WALL_PATTERNS)
            is_floor   = _layer_matches(layer, FLOOR_PATTERNS)
            is_column  = _layer_matches(layer, COLUMN_PATTERNS)
            is_door    = _layer_matches(layer, DOOR_PATTERNS)
            is_window  = _layer_matches(layer, WINDOW_PATTERNS)
            is_beam    = _layer_matches(layer, BEAM_PATTERNS)
            is_stair   = _layer_matches(layer, STAIR_PATTERNS)

            if etype == "LINE":
                s, e = entity.dxf.start, entity.dxf.end
                length = math.sqrt(
                    (e[0]-s[0])**2 + (e[1]-s[1])**2
                )
                if is_wall:
                    wall_length_by_layer[layer] += length
                elif is_beam:
                    beam_length += length

            elif etype == "LWPOLYLINE":
                length, area = _polyline_length_and_area(entity)
                if is_wall:
                    wall_length_by_layer[layer] += length
                elif is_floor and area > 0.5:
                    floor_area_by_layer[layer] += area
                elif is_stair and area > 0.5:
                    stair_area += area
                elif is_beam:
                    beam_length += length
                elif area > 1.0 and not is_door and not is_window:
                    # Untagged closed polylines — likely floor regions
                    floor_area_by_layer['_untagged'] += area

            elif etype == "ARC":
                length = _arc_length(entity)
                if is_wall:
                    wall_length_by_layer[layer] += length

            elif etype == "SPLINE":
                length = _spline_length(entity)
                if is_wall:
                    wall_length_by_layer[layer] += length

            elif etype == "ELLIPSE":
                try:
                    ratio  = abs(entity.dxf.ratio)
                    major  = entity.dxf.major_axis
                    r_maj  = math.sqrt(major[0]**2 + major[1]**2)
                    r_min  = r_maj * ratio
                    h      = ((r_maj - r_min) / (r_maj + r_min)) ** 2
                    perim  = (math.pi * (r_maj + r_min) *
                              (1 + 3*h/(10 + math.sqrt(4-3*h))))
                    if is_wall:
                        wall_length_by_layer[layer] += perim
                except Exception:
                    pass

            elif etype == "CIRCLE":
                if is_column:
                    column_count += 1
                    column_area  += math.pi * entity.dxf.radius ** 2
                elif is_floor:
                    floor_area_by_layer[layer] += (
                        math.pi * entity.dxf.radius ** 2
                    )

            elif etype == "HATCH":
                area = _hatch_area(entity)
                if area > 0.5:
                    if is_floor or is_stair:
                        floor_area_by_layer[layer] += area
                        hatch_areas_found = True
                    elif is_wall:
                        pass  # wall hatches are fill patterns, not area
                    else:
                        floor_area_by_layer['_hatch_untagged'] += area
                        hatch_areas_found = True

            elif etype in ("INSERT",):
                if is_door:
                    door_count += 1
                elif is_window:
                    window_count += 1
                elif is_column:
                    column_count += 1

        except Exception:
            pass

    for entity in all_entities:
        process_entity(entity)
    for entity, layer in extra:
        process_entity(entity, override_layer=layer)

    # Totals
    total_wall_length = sum(wall_length_by_layer.values())
    total_floor_area  = sum(
        v for k, v in floor_area_by_layer.items()
        if v > 0.5  # ignore noise
    )

    # Height extraction
    height, height_source = _extract_height(msp)
    height_used = height if height else 3.0

    # Derived geometry
    total_wall_area    = total_wall_length * height_used
    structural_volume  = total_floor_area  * height_used

    # Confidence scoring
    score = 0
    if total_wall_length > 0:   score += 3
    if total_floor_area  > 0:   score += 3
    if height is not None:       score += 2
    if column_count      > 0:   score += 1
    if hatch_areas_found:        score += 1
    confidence = ("high" if score >= 8 else
                  "medium" if score >= 5 else "low")

    return {
        # Primary geometry
        "totalWallLength":   round(total_wall_length, 2),
        "totalWallArea":     round(total_wall_area, 2),
        "totalFloorArea":    round(total_floor_area, 2),
        "totalColumnCount":  column_count,
        "buildingHeight":    height_used,
        "heightSource":      height_source,
        "structuralVolume":  round(structural_volume, 2),
        "beamLength":        round(beam_length, 2),
        "stairArea":         round(stair_area, 2),
        "doorCount":         door_count,
        "windowCount":       window_count,

        # Per-layer breakdown (for detailed report)
        "wallLengthByLayer": dict(wall_length_by_layer),
        "floorAreaByLayer":  {k: round(v, 2)
                              for k, v in floor_area_by_layer.items()
                              if v > 0.5},

        # Meta
        "confidence":        confidence,
        "confidenceScore":   score,
        "hatchAreasFound":   hatch_areas_found,
        "entityCounts": {
            "walls":   len(wall_length_by_layer),
            "floors":  len(floor_area_by_layer),
            "columns": column_count,
            "doors":   door_count,
            "windows": window_count,
        },
    }


async def parse_from_url(file_url: str) -> dict:
    """Download DXF from Firebase Storage URL and parse it."""
    with tempfile.NamedTemporaryFile(suffix=".dxf", delete=False) as f:
        async with httpx.AsyncClient() as client:
            response = await client.get(file_url, timeout=60.0)
            response.raise_for_status()
            f.write(response.content)
            temp_path = f.name
    try:
        return parse_dxf_file(temp_path)
    finally:
        os.unlink(temp_path)


def parse_from_bytes(file_bytes: bytes) -> dict:
    """Parse DXF from raw bytes (for direct upload without URL)."""
    with tempfile.NamedTemporaryFile(suffix=".dxf", delete=False) as f:
        f.write(file_bytes)
        temp_path = f.name
    try:
        return parse_dxf_file(temp_path)
    finally:
        os.unlink(temp_path)
