#!/usr/bin/env python3
"""Generate PWA icons for ODDO BHF Sales Intelligence"""

import os

# Try to use PIL, fallback to creating simple placeholder
try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("PIL not installed. Creating placeholder SVG icons instead.")

ICON_SIZES = [72, 96, 128, 144, 152, 192, 384, 512]
ICONS_DIR = os.path.join(os.path.dirname(__file__), 'frontend', 'static', 'icons')
PRIMARY_COLOR = (0, 61, 57)  # ODDO BHF Primary Green #003D39
WHITE = (255, 255, 255)

def create_icon_pil(size):
    """Create icon using PIL"""
    # Create image with primary color background
    img = Image.new('RGB', (size, size), PRIMARY_COLOR)
    draw = ImageDraw.Draw(img)

    # Draw "O" for ODDO
    padding = size // 6
    circle_size = size - (padding * 2)

    # Outer circle (white)
    draw.ellipse(
        [padding, padding, padding + circle_size, padding + circle_size],
        outline=WHITE,
        width=max(2, size // 20)
    )

    # Inner text "O" or logo representation
    inner_padding = size // 3
    inner_size = size - (inner_padding * 2)

    # Draw stylized "O"
    draw.ellipse(
        [inner_padding, inner_padding, inner_padding + inner_size, inner_padding + inner_size],
        fill=WHITE
    )

    # Cut out center to make it a ring
    center_padding = size // 2.5
    center_size = size - (int(center_padding) * 2)
    draw.ellipse(
        [int(center_padding), int(center_padding), int(center_padding) + center_size, int(center_padding) + center_size],
        fill=PRIMARY_COLOR
    )

    return img

def create_svg_icon(size):
    """Create SVG icon as fallback"""
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">
  <rect width="{size}" height="{size}" fill="#003D39"/>
  <circle cx="{size//2}" cy="{size//2}" r="{size//3}" fill="none" stroke="white" stroke-width="{max(2, size//20)}"/>
  <text x="{size//2}" y="{size//2 + size//10}" text-anchor="middle" fill="white" font-family="Arial, sans-serif" font-size="{size//3}" font-weight="bold">O</text>
</svg>'''
    return svg

def main():
    os.makedirs(ICONS_DIR, exist_ok=True)

    for size in ICON_SIZES:
        filename = f'icon-{size}x{size}'

        if HAS_PIL:
            # Create PNG icon
            img = create_icon_pil(size)
            png_path = os.path.join(ICONS_DIR, f'{filename}.png')
            img.save(png_path, 'PNG')
            print(f'Created: {png_path}')
        else:
            # Create SVG icon as fallback
            svg = create_svg_icon(size)
            svg_path = os.path.join(ICONS_DIR, f'{filename}.svg')
            with open(svg_path, 'w') as f:
                f.write(svg)
            print(f'Created: {svg_path}')

    # Also create favicon
    if HAS_PIL:
        favicon = create_icon_pil(32)
        favicon_path = os.path.join(ICONS_DIR, 'favicon.ico')
        favicon.save(favicon_path, 'ICO')
        print(f'Created: {favicon_path}')

    print('\nIcon generation complete!')
    print(f'Icons saved to: {ICONS_DIR}')

if __name__ == '__main__':
    main()
