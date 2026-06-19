#!/usr/bin/env python3
"""
export.py

Generate all M1 logo variants from a single Inkscape SVG master file.

For each variant, this script exports:
  - SVG, with embedded RDF/Creative Commons metadata
  - PDF
  - EPS
  - PDF/EPS filtered effects rasterized at 400 dpi
  - PNG at 16, 32, 48, 64, 128, 256, 512, 1024, 2048 px,
    with embedded PNG text metadata and EXIF metadata
  - WebP at the same raster sizes
  - ICO containing 16, 32, 48, 128, 256 px images

Default behavior:
  - Existing export files are skipped.
  - Use --force to overwrite existing export files.

Assumptions:
  - The master file is an Inkscape SVG.
  - Inkscape is installed and available as `inkscape` on PATH.
  - Pillow is installed.
  - The SVG canvas/page is square.
  - Exports should use the SVG page/canvas area, not the drawing bounds.

Usage:
  python export.py --input m1.svg --output dist
  python export.py --input m1.svg --output dist --force
  python export.py --input m1.svg --output dist --verbose
"""

from __future__ import annotations

import argparse
import copy
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterable

from PIL import Image, PngImagePlugin

PREFIX = "m1"

AUTHOR = "Raesangur"
COPYRIGHT = "© 2026 Pascal-Emmanuel Lachance (Raesangur)"
LICENSE_NAME = "Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International"
LICENSE_SHORT = "CC BY-NC-ND 4.0"
LICENSE_URL = "https://creativecommons.org/licenses/by-nc-nd/4.0/"
DESCRIPTION = (
    "Personal logo and brand asset for Raesangur (Pascal-Emmanuel Lachance). "
    "Use as an endorsement, certification, approval mark, identity mark, or brand mark "
    "requires explicit permission."
)

# TIFF/EXIF tag IDs commonly understood by metadata tools.
# PNG stores EXIF in an eXIf chunk; support varies by viewer.
EXIF_IMAGE_DESCRIPTION = 270
EXIF_SOFTWARE = 305
EXIF_ARTIST = 315
EXIF_COPYRIGHT = 33432
EXIF_XP_TITLE = 40091
EXIF_XP_COMMENT = 40092
EXIF_XP_AUTHOR = 40093
EXIF_XP_KEYWORDS = 40094

KNOWN_LAYERS = [
    "main", "outline", "black-white", "pride",
    "Clouds 1", "Clouds 2", "Clouds 3", "White Background",
]

VARIANTS = {
    "alpha": ["main"],
    "black-white": ["black-white", "White Background"],
    "clouds": ["main", "Clouds 1", "Clouds 2", "Clouds 3", "White Background"],
    "pride": ["pride", "Clouds 1", "Clouds 2", "Clouds 3", "White Background"],
    "outline": ["outline", "White Background"],
    "white": ["main", "White Background"],
}

RASTER_SIZES = [32, 256, 512, 1024, 2048]
ICO_SIZES = [16, 32, 48, 128, 256]
VECTOR_FILTER_RASTERIZATION_DPI = 400

SVG_NS = "http://www.w3.org/2000/svg"
INKSCAPE_NS = "http://www.inkscape.org/namespaces/inkscape"
RDF_NS = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
DC_NS = "http://purl.org/dc/elements/1.1/"
CC_NS = "http://creativecommons.org/ns#"

ET.register_namespace("", SVG_NS)
ET.register_namespace("inkscape", INKSCAPE_NS)
ET.register_namespace("rdf", RDF_NS)
ET.register_namespace("dc", DC_NS)
ET.register_namespace("cc", CC_NS)

INKSCAPE_LABEL = f"{{{INKSCAPE_NS}}}label"
RDF_ABOUT = f"{{{RDF_NS}}}about"
RDF_RESOURCE = f"{{{RDF_NS}}}resource"


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[1] if "}" in tag else tag


def title_for_variant(variant_name: str) -> str:
    return f"M1 Logo - {variant_name} variant"


def metadata_fields(variant_name: str) -> dict[str, str]:
    return {
        "Title": title_for_variant(variant_name),
        "Author": AUTHOR,
        "Creator": AUTHOR,
        "Copyright": COPYRIGHT,
        "Description": DESCRIPTION,
        "License": LICENSE_NAME,
        "License Short Name": LICENSE_SHORT,
        "License URL": LICENSE_URL,
    }


def remove_existing_top_level_svg_metadata(root: ET.Element) -> None:
    for child in list(root):
        if local_name(child.tag) == "metadata":
            root.remove(child)


def insert_svg_metadata(root: ET.Element, variant_name: str) -> None:
    remove_existing_top_level_svg_metadata(root)
    metadata = ET.Element(f"{{{SVG_NS}}}metadata")
    rdf = ET.SubElement(metadata, f"{{{RDF_NS}}}RDF")
    work = ET.SubElement(rdf, f"{{{CC_NS}}}Work", {RDF_ABOUT: ""})

    ET.SubElement(work, f"{{{DC_NS}}}title").text = title_for_variant(variant_name)
    ET.SubElement(work, f"{{{DC_NS}}}description").text = DESCRIPTION
    ET.SubElement(work, f"{{{DC_NS}}}format").text = "image/svg+xml"

    creator = ET.SubElement(work, f"{{{DC_NS}}}creator")
    creator_agent = ET.SubElement(creator, f"{{{CC_NS}}}Agent")
    ET.SubElement(creator_agent, f"{{{DC_NS}}}title").text = AUTHOR

    rights = ET.SubElement(work, f"{{{DC_NS}}}rights")
    rights_agent = ET.SubElement(rights, f"{{{CC_NS}}}Agent")
    ET.SubElement(rights_agent, f"{{{DC_NS}}}title").text = COPYRIGHT

    ET.SubElement(work, f"{{{CC_NS}}}license", {RDF_RESOURCE: LICENSE_URL})

    insert_index = 0
    for index, child in enumerate(list(root)):
        if local_name(child.tag) in {"title", "desc"}:
            insert_index = index + 1
    root.insert(insert_index, metadata)


def png_text_metadata(variant_name: str, size: int) -> PngImagePlugin.PngInfo:
    fields = metadata_fields(variant_name)
    fields["Title"] = f"{title_for_variant(variant_name)} - {size}x{size} PNG"
    fields["Pixel Size"] = f"{size}x{size}"
    info = PngImagePlugin.PngInfo()
    for key, value in fields.items():
        info.add_text(key, value, zip=True)
    return info


def windows_xp_exif_string(value: str) -> bytes:
    """Encode an EXIF XP* string as UTF-16LE with a trailing NUL terminator."""
    return (value + "\x00").encode("utf-16le")


def png_exif_metadata(variant_name: str, size: int) -> Image.Exif:
    """Create EXIF metadata for PNG eXIf chunks. Viewer support varies."""
    title = f"{title_for_variant(variant_name)} - {size}x{size} PNG"
    keywords = f"M1 logo; {variant_name}; {LICENSE_SHORT}; Raesangur"
    comment = f"{DESCRIPTION} License: {LICENSE_NAME} ({LICENSE_URL})"

    exif = Image.Exif()
    exif[EXIF_IMAGE_DESCRIPTION] = title
    exif[EXIF_ARTIST] = AUTHOR
    exif[EXIF_COPYRIGHT] = COPYRIGHT
    exif[EXIF_SOFTWARE] = "export.py via Inkscape and Pillow"

    # These Windows XP tags are often shown by consumer-oriented EXIF viewers.
    exif[EXIF_XP_TITLE] = windows_xp_exif_string(title)
    exif[EXIF_XP_AUTHOR] = windows_xp_exif_string(AUTHOR)
    exif[EXIF_XP_KEYWORDS] = windows_xp_exif_string(keywords)
    exif[EXIF_XP_COMMENT] = windows_xp_exif_string(comment)
    return exif


def add_png_metadata_in_place(png_path: Path, variant_name: str, size: int) -> None:
    """Re-save a PNG with both PNG text chunks and PNG eXIf EXIF metadata."""
    with Image.open(png_path) as image:
        dpi = image.info.get("dpi")
        save_kwargs = {
            "pnginfo": png_text_metadata(variant_name, size),
            "exif": png_exif_metadata(variant_name, size).tobytes(),
        }
        if dpi:
            save_kwargs["dpi"] = dpi
        image.save(png_path, "PNG", **save_kwargs)


def parse_style(style: str | None) -> dict[str, str]:
    if not style:
        return {}
    parsed: dict[str, str] = {}
    for part in style.split(";"):
        part = part.strip()
        if part and ":" in part:
            key, value = part.split(":", 1)
            parsed[key.strip()] = value.strip()
    return parsed


def serialize_style(style: dict[str, str]) -> str:
    return ";".join(f"{key}:{value}" for key, value in style.items())


def set_layer_visibility(element: ET.Element, visible: bool) -> None:
    style = parse_style(element.get("style"))
    if visible:
        element.set("display", "inline")
        if style.get("display") == "none":
            del style["display"]
        if style.get("visibility") == "hidden":
            del style["visibility"]
    else:
        element.set("display", "none")
        style["display"] = "none"

    style_text = serialize_style(style)
    if style_text:
        element.set("style", style_text)
    elif "style" in element.attrib:
        del element.attrib["style"]


def find_inkscape_layers(root: ET.Element) -> dict[str, ET.Element]:
    layers: dict[str, ET.Element] = {}
    for element in root.iter():
        if local_name(element.tag) == "g":
            label = element.get(INKSCAPE_LABEL)
            if label:
                layers[label] = element
    return layers


def validate_layers(layer_map: dict[str, ET.Element]) -> None:
    missing = [label for label in KNOWN_LAYERS if label not in layer_map]
    if missing:
        raise RuntimeError("Missing expected Inkscape layer label(s): " + ", ".join(missing))


def write_variant_svg(source_tree: ET.ElementTree, variant_name: str, visible_layers: Iterable[str], output_svg: Path, force: bool) -> bool:
    if output_svg.exists() and not force:
        print(f"  Skipping existing SVG: {output_svg}")
        return False

    tree = copy.deepcopy(source_tree)
    root = tree.getroot()
    layer_map = find_inkscape_layers(root)
    validate_layers(layer_map)

    visible_set = set(visible_layers)
    for label in KNOWN_LAYERS:
        set_layer_visibility(layer_map[label], label in visible_set)

    insert_svg_metadata(root, variant_name)
    output_svg.parent.mkdir(parents=True, exist_ok=True)
    tree.write(output_svg, encoding="utf-8", xml_declaration=True)
    return True


def should_skip(path: Path, force: bool) -> bool:
    return path.exists() and not force


def run_command(command: list[str], verbose: bool = False) -> None:
    if verbose:
        print("  $ " + " ".join(str(part) for part in command))
    subprocess.run(command, check=True)


def export_vector(svg_path: Path, output_path: Path, export_type: str, force: bool, verbose: bool) -> bool:
    if should_skip(output_path, force):
        print(f"  Skipping existing {export_type.upper()}: {output_path}")
        return False

    run_command([
        "inkscape", str(svg_path), f"--export-type={export_type}", "--export-area-page",
        f"--export-dpi={VECTOR_FILTER_RASTERIZATION_DPI}", f"--export-filename={output_path}",
    ], verbose=verbose)
    return True


def export_png(svg_path: Path, output_path: Path, variant_name: str, size: int, force: bool, verbose: bool) -> bool:
    if should_skip(output_path, force):
        print(f"    Skipping existing PNG: {output_path.name}")
        return False

    run_command([
        "inkscape", str(svg_path), "--export-type=png", "--export-area-page",
        f"--export-filename={output_path}", f"--export-width={size}", f"--export-height={size}",
    ], verbose=verbose)
    add_png_metadata_in_place(output_path, variant_name, size)
    return True


def png_to_webp(png_path: Path, webp_path: Path, force: bool) -> bool:
    if should_skip(webp_path, force):
        print(f"    Skipping existing WebP: {webp_path.name}")
        return False
    with Image.open(png_path) as image:
        image.save(webp_path, "WEBP", lossless=True)
    return True


def build_ico(variant_dir: Path, variant_name: str, force: bool) -> bool:
    source_png = variant_dir / f"{PREFIX}_{variant_name}_256.png"
    ico_path = variant_dir / f"{PREFIX}_{variant_name}.ico"
    if should_skip(ico_path, force):
        print(f"  Skipping existing ICO: {ico_path}")
        return False
    with Image.open(source_png) as image:
        image.save(ico_path, format="ICO", sizes=[(size, size) for size in ICO_SIZES])
    return True


def build_assets(input_svg: Path, output_dir: Path, force: bool, verbose: bool) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    source_tree = ET.parse(input_svg)
    validate_layers(find_inkscape_layers(source_tree.getroot()))

    written_count = 0
    skipped_count = 0

    print(f"Input SVG: {input_svg}")
    print(f"Output directory: {output_dir}")
    print(f"Overwrite existing files: {'yes' if force else 'no'}")
    print(f"PDF/EPS filtered-effect rasterization DPI: {VECTOR_FILTER_RASTERIZATION_DPI}")
    print()

    for variant_name, visible_layers in VARIANTS.items():
        print(f"Generating variant: {variant_name}")
        variant_dir = output_dir / variant_name
        variant_dir.mkdir(parents=True, exist_ok=True)
        base_name = f"{PREFIX}_{variant_name}"
        variant_svg = variant_dir / f"{base_name}.svg"
        variant_pdf = variant_dir / f"{base_name}.pdf"
        variant_eps = variant_dir / f"{base_name}.eps"

        print(f"  SVG: {variant_svg}")
        written_count += write_variant_svg(source_tree, variant_name, visible_layers, variant_svg, force)
        skipped_count += int(variant_svg.exists() and not force)

        print(f"  PDF: {variant_pdf}")
        result = export_vector(variant_svg, variant_pdf, "pdf", force, verbose)
        written_count += result; skipped_count += int(not result)

        print(f"  EPS: {variant_eps}")
        result = export_vector(variant_svg, variant_eps, "eps", force, verbose)
        written_count += result; skipped_count += int(not result)

        print("  PNG and WebP:")
        for size in RASTER_SIZES:
            png_path = variant_dir / f"{base_name}_{size}.png"
            webp_path = variant_dir / f"{base_name}_{size}.webp"
            result = export_png(variant_svg, png_path, variant_name, size, force, verbose)
            written_count += result; skipped_count += int(not result)
            result = png_to_webp(png_path, webp_path, force)
            written_count += result; skipped_count += int(not result)

        print(f"  ICO: {variant_dir / f'{base_name}.ico'}")
        result = build_ico(variant_dir, variant_name, force)
        written_count += result; skipped_count += int(not result)
        print()

    print("Done.")
    print(f"Files written: {written_count}")
    print(f"Files skipped: {skipped_count}")
    print(f"Total files considered: {written_count + skipped_count}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate all M1 logo variants from a single Inkscape SVG.")
    parser.add_argument("--input", required=True, type=Path, help="Path to the master Inkscape SVG file.")
    parser.add_argument("--output", required=True, type=Path, help="Directory where generated assets will be written.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing export files instead of skipping them.")
    parser.add_argument("--verbose", action="store_true", help="Print external commands before running them.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    build_assets(args.input, args.output, args.force, args.verbose)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
