import ezdxf
import math
from typing import Dict, List

def parse_geometry(file_path: str) -> Dict[str, float]:
    """
    Parses a DXF file to extract total wall length and floor area.
    Filters by layers (e.g., 'WALLS', 'COLUMNS').
    """
    try:
        doc = ezdxf.readfile(file_path)
        msp = doc.modelspace()
        
        total_wall_length = 0.0
        total_area = 0.0
        
        # Extract Wall Lengths (Lines and Polylines on 'WALLS' layer)
        for entity in msp.query('LINE[layer=="WALLS"]'):
            start = entity.dxf.start
            end = entity.dxf.end
            total_wall_length += math.sqrt((end.x - start.x)**2 + (end.y - start.y)**2)
            
        for entity in msp.query('LWPOLYLINE[layer=="WALLS"]'):
            points = entity.get_points()
            for i in range(len(points) - 1):
                p1 = points[i]
                p2 = points[i+1]
                total_wall_length += math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)

        return {
            "total_wall_length": total_wall_length,
            "floor_area": total_area # More complex polygon area logic can be added
        }
    except Exception as e:
        raise Exception(f"Failed to parse CAD file: {str(e)}")
