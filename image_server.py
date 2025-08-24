import os
import pygame
from flask import Flask, jsonify, request
from PIL import Image
import io
import queue
import threading
import time
import tempfile

# Initialize Flask app
app = Flask(__name__)

# Initialize Pygame in the main thread
pygame.init()

# Initialize Pygame mixer for audio
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)

screen = pygame.display.set_mode((1920, 1080))#, pygame.FULLSCREEN)
pygame.display.set_caption('Image Slideshow')
pygame.display.flip()  # Force initial display update
time.sleep(0.1)  # Brief delay to ensure HDMI/projector is ready

# Directory containing images
IMAGE_DIR = "images"
SOUND_DIR = "sounds"
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(SOUND_DIR, exist_ok=True)

# Load image list
image_files = [f for f in os.listdir(IMAGE_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
image_files.sort()
current_image_index = 0

# Queue for display commands
display_queue = queue.Queue()

# Panning state
panning = False
pan_direction = 0  # -1 for left, 1 for right, 0 for stopped
pan_speed = 200  # Pixels per second (default)
viewport_x = 0  # Current x position of the viewport

# Cached image data
current_surface = None
current_img_width = 0  # Width of original image
tiled_img_width = 0  # Width of tiled (original + flipped) image

def load_image(image_path, target_height=1080):
    """Load and scale image, create tiled surface with flipped version."""
    print(f"Loading image: {image_path}")
    try:
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
        
        # Save to temporary BMP file (Pygame on Raspbian prefers BMP)
        with tempfile.NamedTemporaryFile(suffix='.bmp', delete=False) as tmp_file:
            tiled_img.save(tmp_file.name, format='BMP')
            surface = pygame.image.load(tmp_file.name)
            tmp_file.close()
            os.unlink(tmp_file.name)  # Delete temporary file
        
        print(f"Loaded surface: {image_path}, width={new_width}, tiled_width={new_width * 2}")
        return surface, new_width, new_width * 2
    except Exception as e:
        print(f"Error loading image {image_path}: {e}")
        return None, 0, 0

def display_image(index, reset_viewport=True):
    """Display the image at the given index."""
    global current_surface, current_img_width, tiled_img_width, viewport_x, current_image_index
    print(f"Displaying image: {image_files[index] if image_files else 'No image'}")
    if not image_files:
        screen.fill((0, 0, 0))  # Black screen if no images
        pygame.display.flip()
        return
    
    if reset_viewport:
        viewport_x = 0
    
    image_path = os.path.join(IMAGE_DIR, image_files[index])
    current_surface, current_img_width, tiled_img_width = load_image(image_path)
    
    if current_surface is None:
        print(f"Failed to load image {image_files[index]}, skipping...")
        screen.fill((0, 0, 0))
        pygame.display.flip()
        # Move to next image if available
        if len(image_files) > 1:
            current_image_index = (index + 1) % len(image_files)
            display_image(current_image_index)
        return
    
    # Create a black background
    screen.fill((0, 0, 0))
    
    # Draw the visible portion of the tiled image
    src_x = viewport_x % tiled_img_width
    src_rect = pygame.Rect(src_x, 0, 1920, 1080)
    
    # Handle viewport spanning the boundary
    if src_x + 1920 > tiled_img_width:
        first_width = tiled_img_width - src_x
        screen.blit(current_surface, (0, 0), (src_x, 0, first_width, 1080))
        second_width = 1920 - first_width
        screen.blit(current_surface, (first_width, 0), (0, 0, second_width, 1080))
    else:
        screen.blit(current_surface, (0, 0), src_rect)
    
    pygame.display.flip()
    print(f"Rendered image: {image_files[index]}, viewport_x={viewport_x}")

def play_sound(filename, volume=1.0):
    """Play a sound file with specified volume."""
    sound_path = os.path.join(SOUND_DIR, filename)
    print(f"Attempting to play sound: {sound_path}")
    try:
        if not os.path.exists(sound_path):
            print(f"Error: Sound file {sound_path} not found")
            return False
        sound = pygame.mixer.Sound(sound_path)
        sound.set_volume(min(max(volume, 0.0), 1.0))  # Clamp volume to 0.0–1.0
        sound.play()
        print(f"Playing sound: {filename}, volume={volume}")
        return True
    except Exception as e:
        print(f"Error playing sound {filename}: {e}")
        return False

@app.route('/next', methods=['GET'])
def next_image():
    """Queue the next image to be displayed."""
    global current_image_index, panning
    if image_files:
        current_image_index = (current_image_index + 1) % len(image_files)
        panning = False  # Stop panning when switching images
        display_queue.put(('image', current_image_index))
        return jsonify({"status": "success", "image": image_files[current_image_index], "index": current_image_index})
    return jsonify({"status": "error", "message": "No images available"})

@app.route('/select/<index>', methods=['GET'])
def select_image(index):
    """Queue a specific image by index to be displayed."""
    global current_image_index, panning
    try:
        index = int(index)
        if index < 0 or index >= len(image_files):
            return jsonify({"status": "error", "message": f"Invalid index. Must be between 0 and {len(image_files) - 1}."})
        if image_files:
            current_image_index = index
            panning = False  # Stop panning when selecting image
            display_queue.put(('image', current_image_index))
            return jsonify({"status": "success", "image": image_files[current_image_index], "index": current_image_index})
        return jsonify({"status": "error", "message": "No images available"})
    except ValueError:
        return jsonify({"status": "error", "message": "Invalid index. Must be an integer."})

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

@app.route('/viewport/<x>', methods=['GET'])
def set_viewport(x):
    global viewport_x
    viewport_x = int(x)
    print(f'Set viewport to {viewport_x}')
    return jsonify({"status": "success", "message": "viewport set"})

@app.route('/stop', methods=['GET'])
def stop_pan():
    """Stop panning."""
    global panning
    panning = False
    return jsonify({"status": "success", "message": "Panning stopped"})

@app.route('/set_speed/<speed>', methods=['GET'])
def set_speed(speed):
    """Set the panning speed in pixels per second."""
    try:
        new_speed = float(speed)
        if new_speed <= 0:
            return jsonify({"status": "error", "message": "Speed must be positive."})
        if new_speed > 2000:
            return jsonify({"status": "error", "message": "Speed must not exceed 2000 pixels/second."})
        display_queue.put(('speed', new_speed))
        return jsonify({"status": "success", "speed": new_speed})
    except ValueError:
        return jsonify({"status": "error", "message": "Invalid speed. Must be a number."})

@app.route('/status', methods=['GET'])
def status():
    """Return current image and status."""
    if image_files:
        return jsonify({
            "status": "success",
            "current_image": image_files[current_image_index],
            "current_index": current_image_index,
            "total_images": len(image_files),
            "panning": panning,
            "pan_direction": "left" if pan_direction == -1 else "right" if pan_direction == 1 else "stopped",
            "pan_speed": pan_speed
        })
    return jsonify({"status": "error", "message": "No images available"})

@app.route('/play_sound/<filename>', methods=['GET'])
def play_sound_route(filename):
    """Queue a sound to be played."""
    volume = float(request.args.get('volume', '1.0'))
    if volume < 0 or volume > 1.0:
        return jsonify({"status": "error", "message": "Volume must be between 0.0 and 1.0"}), 400
    display_queue.put(('sound', (filename, volume)))
    return jsonify({"status": "success", "sound": filename, "volume": volume})

def run_flask():
    """Run Flask server in a separate thread."""
    app.run(host='0.0.0.0', port=5000, threaded=True)

def main():
    global panning, viewport_x, current_image_index, pan_direction, pan_speed
    print("Starting main loop")
    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Clear cached surface to ensure clean initialization
    global current_surface, current_img_width, tiled_img_width
    current_surface = None
    current_img_width = 0
    tiled_img_width = 0
    
    # Display initial image
    if image_files:
        print("Displaying initial image")
        display_image(current_image_index)
        # Force a second render to stabilize display
        pygame.display.flip()
    
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
                    src_x = viewport_x % tiled_img_width
                    src_rect = pygame.Rect(src_x, 0, 1920, 1080)
                    screen.fill((0, 0, 0))
                    if src_x + 1920 > tiled_img_width:
                        first_width = tiled_img_width - src_x
                        screen.blit(current_surface, (0, 0), (src_x, 0, first_width, 1080))
                        second_width = 1920 - first_width
                        screen.blit(current_surface, (first_width, 0), (0, 0, second_width, 1080))
                    else:
                        screen.blit(current_surface, (0, 0), src_rect)
                    pygame.display.flip()
                    print(f"Panning update: viewport_x={viewport_x}")
            elif command == 'speed':
                pan_speed = data
                print(f"Panning speed set to: {pan_speed} pixels/second")
            elif command == 'sound':
                filename, volume = data
                if not play_sound(filename, volume):
                    print(f"Failed to play sound: {filename}")
        except queue.Empty:
            pass
        
        # Update panning
        if panning and image_files and current_surface:
            # Update viewport position
            viewport_x += pan_direction * pan_speed * delta_time
            
            # Redraw with continuous viewport
            src_x = viewport_x % tiled_img_width
            src_rect = pygame.Rect(src_x, 0, 1920, 1080)
            screen.fill((0, 0, 0))
            if src_x + 1920 > tiled_img_width:
                first_width = tiled_img_width - src_x
                screen.blit(current_surface, (0, 0), (src_x, 0, first_width, 1080))
                second_width = 1920 - first_width
                screen.blit(current_surface, (first_width, 0), (0, 0, second_width, 1080))
            else:
                screen.blit(current_surface, (0, 0), src_rect)
            pygame.display.flip()
            print(f"Panning: viewport_x={viewport_x}")
    
    pygame.quit()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pygame.quit()
