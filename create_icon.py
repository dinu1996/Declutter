from PIL import Image, ImageDraw

def create_trash_icon(filename="icon.ico"):
    size = (256, 256)
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    # Draw a professional trash can
    # Blue/gray sleek look compatible with dark themes
    primary_color = "#3498db" # Nice blue
    secondary_color = "#bdc3c7" # Light gray
    
    # Bin lid
    draw.rounded_rectangle([30, 60, 226, 80], radius=5, fill=secondary_color)
    
    # Lid handle
    draw.rounded_rectangle([100, 30, 156, 60], radius=5, fill=secondary_color)
    
    # Bin body
    draw.rounded_rectangle([50, 90, 206, 240], radius=15, fill=primary_color)
    
    # Lines on the bin body
    for x in [80, 128, 176]:
        draw.rounded_rectangle([x-5, 110, x+5, 220], radius=3, fill=(255, 255, 255, 100))
        
    image.save(filename, format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
    print(f"Icon generated at {filename}")

if __name__ == "__main__":
    create_trash_icon()
