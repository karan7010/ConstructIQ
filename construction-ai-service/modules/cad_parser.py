"""
Production-grade DXF parser for ConstructIQ.
Handles real architectural floor plans — walls, floors, columns,
doors, windows, beams, stairs, curves, and block references.

Key design principles:
1. EXACT layer name matching for short codes (no substring false positives)
2. Geometric sanity filters (reject implausibly large/small areas)
3. Drawing type detection (reject section/elevation views from floor plan calc)
4. Unit detection from INSUNITS header + bounding box + text annotations
5. Steel from CONCRETE VOLUME only (not structural volume / air space)
"""
import math
import re
import ezdxf
import httpx
import tempfile
import os
from typing import Optional
from collections import defaultdict


# ── LAYER CLASSIFICATION ────────────────────────────────────────────────────
# Rules for _layer_matches():
#   EXACT  — layer must equal the pattern exactly (case-insensitive)
#   PREFIX — layer must START WITH the pattern
#   SUBSTR — layer must CONTAIN the pattern (use sparingly, only unambiguous terms)
#
# Format: ('type', 'pattern')

WALL_RULES = [
    ('exact',  'wall'),
    ('exact',  'walls'),
    ('exact',  '3x4'),         # 3x4 partition — exact only, not 3x4f (furring)
    ('exact',  'gf'),          # ground floor walls
    ('substr', 'a-wall'),
    ('substr', 'arch-wall'),
    ('substr', 'ext_wall'),
    ('substr', 'int_wall'),
    ('substr', 'partition'),
    ('substr', 'masonry'),
    ('substr', 'bearing'),
    ('prefix', 'wl'),
    ('prefix', 'w-'),
    # Non-English
    ('substr', 'cloison'),
    ('substr', 'mur'),
]

FLOOR_RULES = [
    ('exact',  'floor'),
    ('exact',  'slab'),
    ('exact',  'rcc'),
    ('exact',  'deck'),
    ('substr', 'a-flor'),
    ('substr', 'a-slab'),
    ('substr', 'paving'),
    ('substr', 'pavement'),
    ('substr', 'dalle'),
    # Common hatch layer names
    ('exact',  'poch'),        # "poche" = floor fill in French CAD
    ('exact',  'tile'),
]

COLUMN_RULES = [
    ('exact',  'col'),
    ('exact',  'pier'),
    ('exact',  'post'),
    ('substr', 'column'),
    ('substr', 'pillar'),
    ('substr', 's-col'),
    ('substr', 'a-col'),
    ('substr', 'rcc-col'),
    ('substr', 'structure'),
]

DOOR_RULES = [
    ('exact',  'door'),
    ('substr', 'a-door'),
    ('prefix', 'dr'),
    ('substr', 'porte'),
]

WINDOW_RULES = [
    ('exact',  'window'),
    ('exact',  'win'),
    ('substr', 'a-glaz'),
    ('substr', 'glazing'),
    ('substr', 'fenetre'),
]

BEAM_RULES = [
    ('exact',  '2x8'),         # rafters/headers (exact — not matched by '2x8x' etc)
    ('exact',  '2x10'),
    ('exact',  '2x12'),
    ('exact',  '1x10'),
    ('substr', 'w14'),         # steel wide-flange (W14X22, W14X30)
    ('substr', 'w16'),
    ('substr', 'beam'),
    ('substr', 'girder'),
    ('substr', 'joist'),
    ('substr', 'lintel'),
    ('substr', 'rafter'),
    ('substr', 'header'),
    ('substr', 'ridge'),
    ('substr', 'a-beam'),
    ('substr', 'rcc-beam'),
]

STAIR_RULES = [
    ('substr', 'stair'),
    ('substr', 'escalier'),
    ('exact',  'ramp'),
    ('substr', 'step'),
]

# Layers that are NEVER structural (explicitly exclude from all matches)
# These are elevation, section, detail, electrical, plumbing views
EXCLUDE_RULES = [
    ('substr', 'elevation'),
    ('substr', 'elev'),
    ('substr', 'section'),
    ('substr', 'sect'),
    ('substr', 'detail'),
    ('substr', 'front-'),
    ('substr', 'rear-'),
    ('substr', 'side-'),
    ('exact',  'site-plan'),
    ('exact',  'site'),
    ('substr', 'elec'),
    ('substr', 'plumb'),
    ('substr', 'mech'),
    ('substr', 'hvac'),
    ('substr', 'anno'),
    ('substr', 'dim'),
    ('substr', 'text'),
    ('exact',  'borderline'),
    ('exact',  'dashed'),
    ('exact',  'thin'),
    ('exact',  'xxhide'),
    ('exact',  'ceilobj'),
    ('exact',  'elightclg'),
    ('exact',  'elightwall'),
    ('exact',  'arcr'),
    ('exact',  'dimline'),
    ('exact',  'epower'),
    ('exact',  'eswitch'),
    ('exact',  'eline'),
    ('exact',  'djamb'),
    ('exact',  'annobj'),
]


def _layer_matches(layer_name: str, rules: list) -> bool:
    """
    Match a DXF layer name against a list of (type, pattern) rules.
    Types: 'exact', 'prefix', 'substr'
    Case-insensitive.
    """
    name = layer_name.lower().strip()
    for rule_type, pattern in rules:
        if rule_type == 'exact':
            if name == pattern:
                return True
        elif rule_type == 'prefix':
            if name.startswith(pattern):
                return True
        elif rule_type == 'substr':
            if pattern in name:
                return True
    return False


def _is_excluded(layer_name: str) -> bool:
    """Check if a layer is in the exclusion list (section/elevation/detail views)."""
    return _layer_matches(layer_name, EXCLUDE_RULES)

# ── GEOMETRY HELPERS ─────────────────────────────────────────────────────────

# ── GEOMETRY HELPERS ─────────────────────────────────────────────────────────

def _shoelace_area(points: list) -> float:
    n = len(points)
    if n < 3:
        return 0.0
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += points[i][0] * points[j][1]
        area -= points[j][0] * points[i][1]
    return abs(area / 2.0)


def _arc_length(entity, scale: float) -> float:
    try:
        radius = entity.dxf.radius * scale
        start = math.radians(entity.dxf.start_angle)
        end = math.radians(entity.dxf.end_angle)
        if end < start:
            end += 2 * math.pi
        return radius * (end - start)
    except Exception:
        return 0.0


def _spline_length(entity, scale: float) -> float:
    try:
        pts = [(p[0] * scale, p[1] * scale) for p in entity.flattening(0.01)]
        total = 0.0
        for i in range(len(pts) - 1):
            dx = pts[i + 1][0] - pts[i][0]
            dy = pts[i + 1][1] - pts[i][1]
            total += math.sqrt(dx * dx + dy * dy)
        return total
    except Exception:
        return 0.0


def _polyline_length_and_area(entity, scale: float):
    try:
        pts = [(p[0] * scale, p[1] * scale) for p in entity.get_points()]
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


def _hatch_area(entity, scale: float) -> float:
    try:
        total = 0.0
        for path in entity.paths:
            path_type = type(path).__name__
            if 'PolylinePath' in path_type:
                pts = [(v[0] * scale, v[1] * scale) for v in path.vertices]
                total += _shoelace_area(pts)
            elif 'EdgePath' in path_type:
                pts = []
                for edge in path.edges:
                    etype = type(edge).__name__
                    if 'LineEdge' in etype:
                        pts.append((edge.start[0] * scale, edge.start[1] * scale))
                    elif 'ArcEdge' in etype:
                        cx = edge.center[0] * scale
                        cy = edge.center[1] * scale
                        r = edge.radius * scale
                        sa = math.radians(edge.start_angle)
                        ea = math.radians(edge.end_angle)
                        if ea < sa:
                            ea += 2 * math.pi
                        for t in range(8):
                            angle = sa + (ea - sa) * t / 8
                            pts.append((cx + r * math.cos(angle),
                                        cy + r * math.sin(angle)))
                    elif 'SplineEdge' in etype:
                        if hasattr(edge, 'control_points') and edge.control_points:
                            for cp in edge.control_points:
                                pts.append((cp[0] * scale, cp[1] * scale))
                if pts:
                    total += _shoelace_area(pts)
        return total
    except Exception:
        return 0.0


# ── UNIT DETECTION ───────────────────────────────────────────────────────────

def _detect_scale_factor(doc, msp) -> tuple:
    """
    Detect drawing unit and return (scale_to_metres, description).

    Strategy (priority order):
    1. INSUNITS header if it's an unambiguous value (4=mm, 5=cm, 6=m, 2=ft)
    2. Text annotation clues (feet/inches notation vs mm notation)
    3. Bounding box plausibility (buildings are 10–500m across)
    4. INSUNITS=1 fallback based on bbox magnitude
    """
    insunits = doc.header.get('$INSUNITS', 0)

    # Collect bounding box from all LINE entities
    all_x, all_y = [], []
    for e in msp:
        try:
            if e.dxftype() == 'LINE':
                all_x += [e.dxf.start[0], e.dxf.end[0]]
                all_y += [e.dxf.start[1], e.dxf.end[1]]
        except Exception:
            pass

    bbox_w = (max(all_x) - min(all_x)) if all_x else 0
    bbox_h = (max(all_y) - min(all_y)) if all_y else 0
    bbox_max = max(bbox_w, bbox_h)

    # Collect text content
    text_content = []
    for e in msp:
        try:
            if e.dxftype() == 'TEXT':
                text_content.append(e.dxf.text)
            elif e.dxftype() == 'MTEXT':
                text_content.append(e.text)
        except Exception:
            pass
    all_text = ' '.join(text_content).lower()

    # Signal: feet/inches notation ("5'-0\"", "2'6x6'8", "8'0x6'8")
    has_feet_inches = (bool(re.search(r"\d+['\"]\d*", all_text)) or
                       bool(re.search(r"\d+'\-\d+", all_text)))

    # Signal: metric mm notation ("550 HIGH", "900 WIDE", "1200mm")
    has_mm_notation = (bool(re.search(r'\b(mm|high|wide|deep)\b', all_text)) or
                       bool(re.search(r'\b\d{3,4}\s*(high|wide|long)\b', all_text)))

    # Plausibility ranges (a real building is 10–500m across)
    plausible_as_metres = 10 <= bbox_max <= 500
    plausible_as_mm = 10_000 <= bbox_max <= 500_000
    plausible_as_inches = 394 <= bbox_max <= 19_685   # ~10m to ~500m in inches
    plausible_as_feet = 33 <= bbox_max <= 1_640       # ~10m to ~500m in feet

    # 1. Clear INSUNITS header
    if insunits == 4:
        return 0.001, 'millimetres (INSUNITS=4)'
    if insunits == 5:
        return 0.01, 'centimetres (INSUNITS=5)'
    if insunits == 6:
        return 1.0, 'metres (INSUNITS=6)'
    if insunits == 2:
        return 0.3048, 'feet (INSUNITS=2)'

    # 2. Text clues
    if has_feet_inches and not has_mm_notation:
        if plausible_as_inches:
            return 0.0254, 'inches (from feet/inches text + bbox plausibility)'
        if plausible_as_feet:
            return 0.3048, 'feet (from feet/inches text + bbox plausibility)'

    if has_mm_notation and not has_feet_inches:
        if plausible_as_mm:
            return 0.001, 'millimetres (from metric text + bbox plausibility)'

    # 3. Bbox plausibility alone
    if plausible_as_mm and not plausible_as_metres:
        return 0.001, f'millimetres (bbox {bbox_max:.0f} only fits mm scale)'

    if plausible_as_metres and not plausible_as_mm:
        return 1.0, f'metres (bbox {bbox_max:.0f} already in metres range)'

    if plausible_as_inches and has_feet_inches:
        return 0.0254, f'inches (bbox {bbox_max:.0f} + feet/inches text)'

    if plausible_as_mm:
        return 0.001, f'millimetres (bbox {bbox_max:.0f}, defaulting to mm)'

    if plausible_as_inches:
        return 0.0254, f'inches (bbox {bbox_max:.0f}, defaulting to inches)'

    # 4. INSUNITS=1 fallback (often misused to mean "unitless")
    if insunits == 1:
        if bbox_max > 5_000:
            return 0.001, 'millimetres (INSUNITS=1 but large coords → mm)'
        else:
            return 0.0254, 'inches (INSUNITS=1, small bbox → inches)'

    return 0.001, 'millimetres (absolute fallback)'


# ── HEIGHT EXTRACTION ────────────────────────────────────────────────────────

def _extract_height(msp) -> tuple:
    """Extract building storey height from TEXT/MTEXT annotations."""
    height_pattern = re.compile(
        r'(\d+\.?\d*)\s*["\']?\s*(m|mm|ft|feet|meter|metre|\'|\")',
        re.IGNORECASE
    )
    candidates = []
    for entity in msp.query('TEXT MTEXT'):
        try:
            text = (entity.dxf.text
                    if hasattr(entity.dxf, 'text')
                    else entity.text)
            for val_str, unit in height_pattern.findall(text.strip()):
                val = float(val_str)
                if unit.lower() == 'mm':
                    val /= 1000
                elif unit.lower() in ('ft', 'feet', "'"):
                    val *= 0.3048
                if 2.0 <= val <= 6.0:   # storey height range: 2m–6m
                    candidates.append(val)
        except Exception:
            continue

    if candidates:
        from collections import Counter
        best = Counter([round(v, 1) for v in candidates]).most_common(1)[0][0]
        return best, 'extracted from drawing annotations'
    return None, 'default 3.0m — no storey height annotation found'


# ── MAIN PARSER ──────────────────────────────────────────────────────────────

def parse_dxf_file(file_path: str) -> dict:
    """
    Parse a DXF file and return comprehensive geometry breakdown.
    All returned measurements are in metres and square metres.
    """
    doc = ezdxf.readfile(file_path)
    msp = doc.modelspace()

    # Step 1: detect unit FIRST — apply to all coordinate reads
    scale, scale_description = _detect_scale_factor(doc, msp)
    print(f'Unit detection: {scale_description} (scale={scale})')

    # Step 2: collect geometry, classifying each entity by layer rules
    wall_length_by_layer = defaultdict(float)
    floor_area_by_layer  = defaultdict(float)
    column_count = 0
    door_count   = 0
    window_count = 0
    beam_length  = 0.0
    stair_area   = 0.0
    hatch_found  = False

    hatch_found  = False

    def process_entity(entity, override_layer=None):
        nonlocal column_count, door_count, window_count
        nonlocal beam_length, stair_area, hatch_found

        try:
            layer = override_layer or getattr(entity.dxf, 'layer', '0')
            etype = entity.dxftype()

            # Hard exclude: section/elevation/detail layers
            if _is_excluded(layer):
                return

            is_wall   = _layer_matches(layer, WALL_RULES)
            is_floor  = _layer_matches(layer, FLOOR_RULES)
            is_col    = _layer_matches(layer, COLUMN_RULES)
            is_door   = _layer_matches(layer, DOOR_RULES)
            is_win    = _layer_matches(layer, WINDOW_RULES)
            is_beam   = _layer_matches(layer, BEAM_RULES)
            is_stair  = _layer_matches(layer, STAIR_RULES)

            if etype == 'LINE':
                s, e = entity.dxf.start, entity.dxf.end
                ln = math.sqrt((e[0] - s[0]) ** 2 + (e[1] - s[1]) ** 2) * scale
                # Sanity filter: ignore lines shorter than 5cm or longer than 500m
                if not (0.05 <= ln <= 500):
                    return
                if is_wall:
                    wall_length_by_layer[layer] += ln
                elif is_beam:
                    beam_length += ln

            elif etype == 'LWPOLYLINE':
                ln, area = _polyline_length_and_area(entity, scale)
                # Sanity filter on area: ignore single-room-sized or building-envelope outliers
                # Legitimate room: 1m² – 5000m²  (e.g. a sports hall)
                # Site boundaries, title blocks etc are usually >10,000m²
                if is_wall:
                    wall_length_by_layer[layer] += ln
                elif is_floor and 1.0 <= area <= 5000:
                    floor_area_by_layer[layer] += area
                    hatch_found = True
                elif is_stair and area > 1.0:
                    stair_area += area
                elif is_beam:
                    beam_length += ln
                # Fallback: closed polylines not tagged as anything specific
                # Only count if area is plausible room size and layer is not excluded
                elif entity.is_closed and 2.0 <= area <= 500 and not any(
                    [is_col, is_door, is_win, is_beam, is_stair]
                ):
                    floor_area_by_layer['_untagged'] += area

            elif etype == 'ARC':
                if is_wall:
                    wall_length_by_layer[layer] += _arc_length(entity, scale)

            elif etype == 'SPLINE':
                if is_wall:
                    wall_length_by_layer[layer] += _spline_length(entity, scale)

            elif etype == 'ELLIPSE':
                try:
                    ratio = abs(entity.dxf.ratio)
                    major = entity.dxf.major_axis
                    r_maj = math.sqrt(major[0] ** 2 + major[1] ** 2) * scale
                    r_min = r_maj * ratio
                    h = ((r_maj - r_min) / (r_maj + r_min)) ** 2
                    perim = (math.pi * (r_maj + r_min) *
                             (1 + 3 * h / (10 + math.sqrt(4 - 3 * h))))
                    if is_wall:
                        wall_length_by_layer[layer] += perim
                except Exception:
                    pass

            elif etype == 'CIRCLE':
                if is_col:
                    column_count += 1
                elif is_floor:
                    r = entity.dxf.radius * scale
                    floor_area_by_layer[layer] += math.pi * r * r

            elif etype == 'HATCH':
                area = _hatch_area(entity, scale)
                if area > 0.5:
                    if is_floor or is_stair:
                        if area <= 5000:   # sanity: reject site-level hatches
                            floor_area_by_layer[layer] += area
                            hatch_found = True
                    elif not is_wall and not is_col:
                        if 1.0 <= area <= 500:
                            floor_area_by_layer['_hatch'] += area
                            hatch_found = True

            elif etype == 'INSERT':
                if is_door:
                    door_count += 1
                elif is_win:
                    window_count += 1
                elif is_col:
                    column_count += 1

        except Exception:
            pass

    # Process all entities in modelspace
    for e in msp:
        process_entity(e)

    # Expand block inserts
    try:
        for ins in msp.query('INSERT'):
            bname = ins.dxf.name
            if bname in doc.blocks:
                for be in doc.blocks[bname]:
                    process_entity(be, override_layer=ins.dxf.layer)
    except Exception:
        pass

    # Step 3: post-processing

    total_wall_length = sum(wall_length_by_layer.values())
    total_floor_area  = sum(v for v in floor_area_by_layer.values() if v > 0.5)

    # Floor area fallback for LINE-only drawings (no hatches, no closed polylines)
    floor_area_source = 'from geometry (hatch/polyline)'
    if (total_floor_area < 20.0 and total_wall_length > 50) or total_floor_area < 2.0:
        # Build bounding box from classified wall lines only
        wall_xs, wall_ys = [], []
        for e in msp:
            try:
                layer = getattr(e.dxf, 'layer', '0')
                if (layer in wall_length_by_layer and
                        e.dxftype() == 'LINE'):
                    wall_xs += [e.dxf.start[0] * scale, e.dxf.end[0] * scale]
                    wall_ys += [e.dxf.start[1] * scale, e.dxf.end[1] * scale]
            except Exception:
                pass

        if wall_xs:
            bw = max(wall_xs) - min(wall_xs)
            bh = max(wall_ys) - min(wall_ys)
            # 65% space efficiency — walls + corridors + structure occupy ~35%
            inferred = bw * bh * 0.65
            if inferred > 2.0:
                total_floor_area = inferred
                floor_area_source = (f'estimated from wall bbox '
                                     f'({bw:.1f}m × {bh:.1f}m × 0.65)')

    # Step 4: extract height
    height, h_source = _extract_height(msp)
    h = height if height else 3.0

    # Step 5: derived geometry
    total_wall_area   = total_wall_length * h
    # CORRECT: concrete volume = slab thickness × floor area
    # NOT structural_volume (which includes air space in rooms)
    concrete_volume   = total_floor_area * 0.15   # 150mm M20 slab

    # Step 6: confidence scoring
    score = 0
    if total_wall_length > 0:  score += 3
    if total_floor_area  > 0:  score += 3
    if height is not None:     score += 2
    if column_count > 0:       score += 1
    if hatch_found:            score += 1
    confidence = ('high'   if score >= 8 else
                  'medium' if score >= 5 else 'low')

    return {
        # Unit info
        'unitDetected':       scale_description,
        'scaleApplied':       scale,

        # Geometry
        'totalWallLength':    round(total_wall_length, 2),
        'totalWallArea':      round(total_wall_area, 2),
        'totalFloorArea':     round(total_floor_area, 2),
        'floorAreaSource':    floor_area_source,
        'concreteVolume':     round(concrete_volume, 2),
        'totalColumnCount':   column_count,
        'buildingHeight':     h,
        'heightSource':       h_source,
        'structuralVolume':   round(total_floor_area * h, 2),   # for reference only
        'beamLength':         round(beam_length, 2),
        'stairArea':          round(stair_area, 2),
        'doorCount':          door_count,
        'windowCount':        window_count,

        # Per-layer breakdowns (useful for debugging and detailed report)
        'wallLengthByLayer':  {k: round(v, 2) for k, v in wall_length_by_layer.items()},
        'floorAreaByLayer':   {k: round(v, 2) for k, v in floor_area_by_layer.items()
                               if v > 0.5},

        # Quality
        'confidence':         confidence,
        'confidenceScore':    score,
        'hatchAreasFound':    hatch_found,
        'entityCounts': {
            'walls':   len(wall_length_by_layer),
            'floors':  len(floor_area_by_layer),
            'columns': column_count,
            'doors':   door_count,
            'windows': window_count,
        },
    }


# ── FILE INTAKE ──────────────────────────────────────────────────────────────

async def parse_from_url(file_url: str) -> dict:
    """Download DXF from Firebase Storage URL and parse."""
    with tempfile.NamedTemporaryFile(suffix='.dxf', delete=False) as f:
        async with httpx.AsyncClient() as client:
            r = await client.get(file_url, timeout=60.0)
            r.raise_for_status()
            f.write(r.content)
            tmp = f.name
    try:
        return parse_dxf_file(tmp)
    finally:
        os.unlink(tmp)


def parse_from_bytes(file_bytes: bytes) -> dict:
    """Parse DXF from raw bytes — used by /parse-cad-upload endpoint."""
    with tempfile.NamedTemporaryFile(suffix='.dxf', delete=False) as f:
        f.write(file_bytes)
        tmp = f.name
    try:
        return parse_dxf_file(tmp)
    finally:
        os.unlink(tmp)
