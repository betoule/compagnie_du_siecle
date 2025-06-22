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

# Panning state
panning = False
pan_direction = 0  # -1 for left, 1 for right, 0 for stopped
pan_speed = 200  # Pixels per second
viewport_x = 0  # Current x position of the viewport

# Cached image data
current_surface = None
current_img_width = 0  # Width of original image
tiled_img_width = 0  # Width of tiled (original + flipped) image

def load_image(image_path, target_height=1080):
    """Load and scale image, create tiled surface with flipped version."""
    img = Image.open(image_path)
    img_width, img_height = img.size
    aspect_ratio = target_height / img_height
    new_width = int(img_width * aspect_ratio)
    img = img.resize((new_width, target_height), Image.Resampling.BILINEAR)
    
    # Create flipped image
    flipped_img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    
    # Create tiled image (original + flipped)
    tiled_img = Image.new('RGB', (new_width * 2, target_height))
    tiled_img.paste(img, (0, 0))
    tiled_img.paste(flipped_img, (new_width, 0))
    
    # Convert to Pygame surface
    img_byte_arr = io.BytesIO()
    tiled_img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return pygame.image.load(img_byte_arr), new_width, new_width * 2

def display_image(index, reset_viewport=True):
    """Display the image at the given index."""
    global current_surface, current_img_width, tiled_img_width, viewport_x
    print(f"Displaying image: {image_files[index] if image_files else 'No image'}")
    if not image_files:
        screen.fill((0, 0, 0))  # Black screen if no images
        pygame.display.flip()
        return
    
    if reset_viewport:
        viewport_x = 0
    
    image_path = os.path.join(IMAGE_DIR, image_files[index])
    current_surface, current_img_width, tiled_img_width = load_image(image_path)
    
    # Create a black background
    screen.fill((0, 0, 0))
    
    # Draw the visible portion of the tiled image
    src_x = viewport_x % current_img_width  # Wrap within original image width
    src_rect = pygame.Rect(src_x, 0, 1920, 1080)
    screen.blit(current_surface, (0, 0), src_rect)
    pygame.display.flip()

@app.route('/next', methods=['GET'])
def next_image():
    """Queue the next image to be displayed."""
    global current_image_index, panning
    if image_files:
        current_image_index = (current_image_index + 1) % len(image_files)
        panning = False  # Stop panning when switching images
        display_queue.put(('image', current_image_index))
        return jsonify({"status": "success", "image": image_files[current_image_index]})
    return jsonify({"status": "error", "message": "No images available"})

@app.route('/pan/<direction>', methods=['GET'])
def pan_image(direction):
    """Start panning in the specified direction."""
    global panning, pan_direction
    if image_files:
        if direction.lower() == 'left':
            pan_direction = -1
        elif direction.lower() == 'right':
            pan_direction = 1
        else:
            return jsonify({"status": "error", "message": "Invalid direction. Use 'left' or 'right'."})
        panning = True
        display_queue.put(('pan', None))  # Trigger display update
        return jsonify({"status": "success", "direction": direction})
    return jsonify({"status": "error", "message": "No images available"})

@app.route('/stop', methods=['GET'])
def stop_pan():
    """Stop panning."""
    global panning
    panning = False
    return jsonify({"status": "success", "message": "Panning stopped"})

@app.route('/status', methods=['GET'])
def status():
    """Return current image and status."""
    if image_files:
        return jsonify({
            "status": "success",
            "current_image": image_files[current_image_index],
            "total_images": len(image_files),
            "panning": panning,
            "pan_direction": "left" if pan_direction == -1 else "right" if pan_direction == 1 else "stopped"
        })
    return jsonify({"status": "error", "message": "No images available"})

def run_flask():
    """Run Flask server in a separate thread."""
    app.run(host='0.0.0.0', port=5000, threaded=True)

def main():
    global panning, viewport_x, current_image_index, pan_direction
    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Display initial image
    if image_files:
        display_image(current_image_index)
    
    # Main Pygame loop in the main thread
    clock = pygame.time.Clock()
    running = True
    last_time = time.time()
    while running:
        # Cap framerate at 30 FPS
        clock.tick(30)
        
        # Calculate delta time
        current_time = time.time()
        delta_time = current_time - last_time
        last_time = current_time
        
        # Handle Pygame events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
        
        # Process display commands
        try:
            command, data = display_queue.get_nowait()
            if command == 'image':
                display_image(data)
            elif command == 'pan':
                if current_surface:
                    src_x = viewport_x % current_img_width  # Wrap within original image width
                    src_rect = pygame.Rect(src_x, 0, 1920, 1080)
                    screen.fill((0, 0, 0))
                    screen.blit(current_surface, (0, 0), src_rect)
                    pygame.display.flip()
        except queue.Empty:
            pass
        
        # Update panning
        if panning and image_files and current_surface:
            # Update viewport position
            viewport_x += pan_direction * pan_speed * delta_time
            # Ensure viewport_x stays positive and wraps within original image width
            viewport_x = viewport_x % current_img_width
            if viewport_x < 0:
                viewport_x += current_img_width
            
            # Redraw with wrapped viewport
            src_x = viewport_x % current_img_width
            src_rect = pygame.Rect(src_x, 0, 1920, 1080)
            screen.fill((0, 0, 0))
            screen.blit(current_surface, (0, 0), src_rect)
            pygame.display.flip()
    
    pygame.quit()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pygame.quit()