import ezdxf
import sys
from collections import Counter

def diagnostic(file_path):
    print(f"Analyzing {file_path}...")
    try:
        doc = ezdxf.readfile(file_path)
        msp = doc.modelspace()
        
        entities = list(msp)
        print(f"Total entities: {len(entities)}")
        
        types = Counter([e.dxftype() for e in entities])
        print("\nEntity Type Breakdown:")
        for etype, count in types.most_common():
            print(f"  {etype}: {count}")
            
        layer_0_entities = [e for e in entities if e.dxf.layer == '0']
        print(f"\nEntities on Layer '0': {len(layer_0_entities)}")
        
        # Sample some coordinates to check units
        print("\nCoordinate Samples (Layer '0'):")
        count = 0
        for e in layer_0_entities:
            if count < 10:
                etype = e.dxftype()
                print(f"  {etype} | Layer: {e.dxf.layer}")
                try:
                    if hasattr(e, 'vertices'):
                        verts = list(e.vertices)
                        print(f"    Vertex count: {len(verts)}")
                        if len(verts) > 0:
                            print(f"    First location: {verts[0].dxf.location}")
                    else:
                        print(f"    No vertices attribute")
                except Exception as ve:
                    print(f"    Error reading vertices: {ve}")
                count += 1
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    diagnostic(r"c:\Users\sukhs\OneDrive\Documents\8th_Sem_Project\00-6030-08 Costco 531 S Mississauga, ON - Washroom Remodel -Architectural.dxf")
