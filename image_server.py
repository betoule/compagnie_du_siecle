import os
import pygame
from flask import Flask, jsonify
from PIL import Image
import io
import queue
import threading
import time

# Initialize Flask app
app = Flask(__name__)

# Initialize Pygame in the main thread
pygame.init()
screen = pygame.display.set_mode((1920, 1080), pygame.FULLSCREEN)
pygame.display.set_caption('Image Slideshow')

# Directory containing images
IMAGE_DIR = "images"
os.makedirs(IMAGE_DIR, exist_ok=True)

# Load image list
image_files = [f for f in os.listdir(IMAGE_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
current_image_index = 0

# Queue for display commands
display_queue = queue.Queue()

def resize_image(image_path, target_width=1920, target_height=1080):
    """Resize image to fit 1920x1080 while maintaining aspect ratio."""
    img = Image.open(image_path)
    
    # Calculate aspect ratio
    img_width, img_height = img.size
    aspect_ratio = min(target_width / img_width, target_height / img_height)
    
    # Resize image
    new_width = int(img_width * aspect_ratio)
    new_height = int(img_height * aspect_ratio)
    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Create a black background
    background = Image.new('RGB', (target_width, target_height), (0, 0, 0))
    
    # Paste image in the center
    offset = ((target_width - new_width) // 2, (target_height - new_height) // 2)
    background.paste(img, offset)
    
    # Convert to Pygame surface
    img_byte_arr = io.BytesIO()
    background.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return pygame.image.load(img_byte_arr)

def display_image(index):
    """Display the image at the given index."""
    print(f"Displaying image: {image_files[index] if image_files else 'No image'}")
    if not image_files:
        screen.fill((0, 0, 0))  # Black screen if no images
        pygame.display.flip()
        return
    
    image_path = os.path.join(IMAGE_DIR, image_files[index])
    surface = resize_image(image_path)
    screen.blit(surface, (0, 0))
    pygame.display.flip()

@app.route('/next', methods=['GET'])
def next_image():
    """Queue the next image to be displayed."""
    global current_image_index
    if image_files:
        current_image_index = (current_image_index + 1) % len(image_files)
        display_queue.put(current_image_index)
        return jsonify({"status": "success", "image": image_files[current_image_index]})
    return jsonify({"status": "error", "message": "No images available"})

@app.route('/status', methods=['GET'])
def status():
    """Return current image and status."""
    if image_files:
        return jsonify({"status": "success", "current_image": image_files[current_image_index], "total_images": len(image_files)})
    return jsonify({"status": "error", "message": "No images available"})

def run_flask():
    """Run Flask server in a separate thread."""
    app.run(host='0.0.0.0', port=5000, threaded=True)

def main():
    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Display initial image
    if image_files:
        display_image(current_image_index)
    
    # Main Pygame loop in the main thread
    running = True
    while running:
        # Handle Pygame events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
        
        # Check for display commands
        try:
            index = display_queue.get_nowait()
            display_image(index)
        except queue.Empty:
            pass
        
        # Small delay to prevent CPU overuse
        time.sleep(0.01)
    
    pygame.quit()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pygame.quit()