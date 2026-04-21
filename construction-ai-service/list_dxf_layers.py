import ezdxf
import sys

def list_layers(file_path):
    print(f"Reading {file_path} for layers...")
    try:
        doc = ezdxf.readfile(file_path)
        layers = [layer.dxf.name for layer in doc.layers]
        print(f"Found {len(layers)} layers:")
        for layer in sorted(layers):
            print(f"  - {layer}")
            
        msp = doc.modelspace()
        entities = len(msp)
        print(f"\nTotal entities in ModelSpace: {entities}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_layers(r"c:\Users\sukhs\OneDrive\Documents\8th_Sem_Project\00-6030-08 Costco 531 S Mississauga, ON - Washroom Remodel -Architectural.dxf")
