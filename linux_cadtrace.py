import os
import sys
import cv2
import ezdxf
import ezdxf.math
from PIL import Image
from svgpathtools import svg2paths2
from ezdxf.math import Vec2


# Convert image to PBM (bitmap format for Potrace)
def convert_to_pbm(image_path):
    img = Image.open(image_path).convert('L')  # Convert to grayscale
    bw = img.point(lambda x: 0 if x < 128 else 255, '1')  # Binarize
    pbm_path = os.path.splitext(image_path)[0] + ".pbm"
    bw.save(pbm_path)
    return pbm_path

# Run Potrace to generate SVG from PBM
def trace_with_potrace(pbm_path):
    svg_path = pbm_path.replace(".pbm", ".svg")
    os.system(f"potrace {pbm_path} -s -o {svg_path}")
    return svg_path

# Very basic DXF conversion (placeholder – could parse SVG instead)
def svg_to_dxf(svg_path, dxf_path, samples_per_curve=40):
    print(f"[SVG→DXF] Parsing SVG from: {svg_path}")

    # Parse SVG file with svg2paths2 (includes attributes)
    try:
        paths, attributes, svg_attr = svg2paths2(svg_path)
    except Exception as e:
        print(f"Error reading SVG: {e}")
        return

    if not paths:
        print("No paths found in SVG.")
        return

    # Create new DXF file
    doc = ezdxf.new(dxfversion="R2010")
    msp = doc.modelspace()

    path_count = 0
    for path in paths:
        coords = []
        for segment in path:
            for t in [i / samples_per_curve for i in range(samples_per_curve + 1)]:
                point = segment.point(t)
                coords.append((point.real, -point.imag))  # flip Y for DXF (optional)

        # Remove near-duplicate points
        simplified = [Vec2(*coords[0])]
        for pt in coords[1:]:
            if Vec2(*pt).distance(simplified[-1]) > 0.1:
                simplified.append(Vec2(*pt))

        if len(simplified) >= 2:
            msp.add_lwpolyline(simplified, close=True)
            path_count += 1

    if path_count > 0:
        doc.saveas(dxf_path)
        print(f"[✔] DXF saved to: {dxf_path} with {path_count} polylines.")
    else:
        print("[!] No valid paths found to write to DXF.")

def svg_path_to_dxf_coords(path_obj, samples=100):
    coords = []
    for segment in path_obj:
        for t in [i / samples for i in range(samples + 1)]:
            point = segment.point(t)
            coords.append((point.real, point.imag))
    return coords

def svg_to_dxf(svg_path, dxf_path):
    print(f"Parsing SVG from {svg_path}")
    paths, attributes, svg_attributes = svg2paths2(svg_path)

    doc = ezdxf.new(dxfversion="R2010")
    msp = doc.modelspace()

    for path in paths:
        coords = svg_path_to_dxf_coords(path)
        # Reduce redundant points
        simplified = [Vec2(*coords[0])]
        for pt in coords[1:]:
            if Vec2(*pt).distance(simplified[-1]) > 0.5:  # avoid duplicates
                simplified.append(Vec2(*pt))
        if len(simplified) >= 2:
            msp.add_lwpolyline(simplified, close=True)

    doc.saveas(dxf_path)
    print(f"✅ DXF vector tracing saved to: {dxf_path}")

def main(image_path):
    if not os.path.exists(image_path):
        print("Image file not found.")
        return

    print(f"[1] Preprocessing {image_path}")
    pbm_path = convert_to_pbm(image_path)

    print(f"[2] Tracing with Potrace")
    svg_path = trace_with_potrace(pbm_path)

    print(f"[3] Exporting to DXF (placeholder logic)")
    dxf_path = svg_path.replace(".svg", ".dxf")
    svg_to_dxf(svg_path, dxf_path)

    print("Done.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python linux_cad_trace.py input_image.png")
    else:
        main(sys.argv[1])
