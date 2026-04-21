import os
import sys
import json
from modules.cad_parser import parse_dxf_file
from modules.estimation_engine import calculate_materials, calculate_labour

def main():
    # The file path found earlier
    file_path = r"c:\Users\sukhs\OneDrive\Documents\8th_Sem_Project\00-6030-08 Costco 531 S Mississauga, ON - Washroom Remodel -Architectural.dxf"
    
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return

    print(f"--- Parsing File: {os.path.basename(file_path)} ---")
    
    try:
        # Step 1: Parse the CAD file
        geometry = parse_dxf_file(file_path)
        print("Parsing successful!")
        
        # Debug: Print found layers
        print("\n--- Layers Found ---")
        if "wallLengthByLayer" in geometry:
            print(f"Wall Layers: {list(geometry['wallLengthByLayer'].keys())}")
        if "floorAreaByLayer" in geometry:
            print(f"Floor Layers: {list(geometry['floorAreaByLayer'].keys())}")
        
        # Step 2: Calculate materials
        materials_result = calculate_materials(geometry)
        
        # Step 3: Calculate labour
        labour = calculate_labour(materials_result["materials"], geometry)
        
        # Combine results
        result = {
            "success": True,
            "filename": os.path.basename(file_path),
            "geometry": geometry,
            "materials": materials_result["materials"],
            "labour": labour,
            "confidence": geometry.get("confidence", "unknown")
        }
        
        print("\n--- Estimation Results ---")
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"Error during parsing/estimation: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
