import ezdxf
import os

def create_sample_dxf(filename="docs/sample_floor_plan.dxf"):
    # Ensure it's relative to the project root (where the script is running from's parent)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_path = os.path.join(project_root, filename)
    
    # Ensure docs dir exists
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    
    doc = ezdxf.new()
    msp = doc.modelspace()
    
    # Create walls layer
    doc.layers.add(name="WALLS", color=1)
    
    # Add some walls (Lines) - forming a rectangle
    msp.add_line((0, 0), (10, 0), dxfattribs={'layer': 'WALLS'})
    msp.add_line((10, 0), (10, 10), dxfattribs={'layer': 'WALLS'})
    msp.add_line((10, 10), (0, 10), dxfattribs={'layer': 'WALLS'})
    msp.add_line((0, 10), (0, 0), dxfattribs={'layer': 'WALLS'})
    
    # Add an internal wall
    msp.add_line((0, 5), (5, 5), dxfattribs={'layer': 'WALLS'})
    
    doc.saveas(target_path)
    print(f"Sample DXF created: {target_path}")

if __name__ == "__main__":
    create_sample_dxf()
