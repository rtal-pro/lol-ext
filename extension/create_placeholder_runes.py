import os
import sys
from PIL import Image, ImageDraw, ImageFont
import json

# Create target directory
runes_dir = '/home/rod/Projects/lol-ext/extension/assets/runes'
os.makedirs(runes_dir, exist_ok=True)

# Define colors for different rune paths
path_colors = {
    # Paths
    '8000': (200, 170, 110),  # Precision - Gold
    '8100': (202, 62, 63),    # Domination - Red
    '8200': (158, 124, 201),  # Sorcery - Purple
    '8300': (73, 170, 185),   # Inspiration - Teal
    '8400': (77, 139, 124)    # Resolve - Green
}

# Function to create a colored placeholder with text
def create_placeholder(id, color=(100, 100, 100)):
    filename = os.path.join(runes_dir, f"{id}.png")
    
    # Skip if file already exists and has content
    if os.path.exists(filename) and os.path.getsize(filename) > 0:
        print(f"Skipping {id}.png - already exists")
        return
    
    # Create a new image with transparent background
    size = (128, 128)
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw a circle with the path color
    circle_color = (*color, 220)  # Add alpha channel
    draw.ellipse((10, 10, size[0]-10, size[1]-10), fill=circle_color)
    
    # Add a border
    border_color = (*color, 255)  # Solid color for border
    draw.ellipse((10, 10, size[0]-10, size[1]-10), outline=border_color, width=3)
    
    # Add text (first character of the ID)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 48)
    except IOError:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
        except IOError:
            font = ImageFont.load_default()
    
    # Use the ID as text
    text = str(id)[-2:] if len(str(id)) > 2 else str(id)
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    text_position = ((size[0] - text_width) // 2, (size[1] - text_height) // 2)
    
    # Draw text with a slight shadow for better visibility
    shadow_offset = 2
    draw.text((text_position[0] + shadow_offset, text_position[1] + shadow_offset), 
              text, fill=(0, 0, 0, 180), font=font)
    draw.text(text_position, text, fill=(255, 255, 255, 255), font=font)
    
    # Save the image
    img.save(filename, "PNG")
    print(f"Created placeholder for {id}.png")

# List of rune IDs to create placeholders for
rune_ids = [
    # Paths
    8000, 8100, 8200, 8300, 8400,
    
    # Precision keystones and runes
    8005, 8008, 8021, 8010, 9101, 9111, 8009, 9104, 9105, 9103, 8014, 8017, 8299,
    
    # Domination keystones and runes
    8112, 8128, 9923, 8126, 8139, 8143, 8137, 8140, 8141, 8135, 8105, 8106,
    
    # Sorcery keystones and runes
    8214, 8229, 8230, 8224, 8226, 8275, 8210, 8234, 8233, 8237, 8232, 8236,
    
    # Inspiration keystones and runes
    8351, 8360, 8369, 8306, 8304, 8321, 8313, 8352, 8345, 8347, 8410, 8316,
    
    # Resolve keystones and runes
    8437, 8439, 8465, 8446, 8463, 8401, 8429, 8444, 8473, 8451, 8453, 8242
]

# Function to determine the color based on the rune ID
def get_rune_color(rune_id):
    # Convert to string for comparison
    id_str = str(rune_id)
    
    # Check if it's a path ID first
    if id_str in path_colors:
        return path_colors[id_str]
    
    # Otherwise, determine based on the first digit
    first_digit = id_str[0]
    
    if first_digit == '8':
        second_digit = id_str[1] if len(id_str) > 1 else '0'
        if second_digit == '0':
            return path_colors['8000']  # Precision
        elif second_digit == '1':
            return path_colors['8100']  # Domination
        elif second_digit == '2':
            return path_colors['8200']  # Sorcery
        elif second_digit == '3':
            return path_colors['8300']  # Inspiration
        elif second_digit == '4':
            return path_colors['8400']  # Resolve
    elif first_digit == '9':
        # For 9000 series runes, use a heuristic based on the last two digits
        last_two = int(id_str[-2:]) % 5
        if last_two == 0:
            return path_colors['8000']  # Precision
        elif last_two == 1:
            return path_colors['8100']  # Domination
        elif last_two == 2:
            return path_colors['8200']  # Sorcery
        elif last_two == 3:
            return path_colors['8300']  # Inspiration
        elif last_two == 4:
            return path_colors['8400']  # Resolve
    
    # Default color - gray
    return (150, 150, 150)

# Create placeholders for all rune IDs
for rune_id in rune_ids:
    color = get_rune_color(rune_id)
    create_placeholder(rune_id, color)

print(f"Created {len(rune_ids)} placeholder images in {runes_dir}")