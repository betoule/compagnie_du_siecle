import os
import pygame
from flask import Flask, jsonify, request
from PIL import Image
import io
import queue
import threading
import time
import tempfile
import sys

# Initialize Flask app
app = Flask(__name__)

# Initialize Pygame in the main thread
pygame.init()

# Initialize Pygame mixer for audio
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)

if (len(sys.argv) > 1) and (sys.argv[1] == '--full'):
    display_size = 1920, 1080
    screen = pygame.display.set_mode((display_size[0], display_size[1]), pygame.FULLSCREEN)
else:
    display_size = 640, 480
    screen = pygame.display.set_mode((display_size[0], display_size[1]))

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
print(image_files)
current_image_index = 0

# Queue for display commands
display_queue = queue.Queue()

# Panning state
panning_x = False
pan_direction_x = 0  # -1 for left, 1 for right, 0 for stopped
panning_y = False
pan_direction_y = 0  # -1 for up, 1 for down, 0 for stopped
pan_speed = 200  # Pixels per second (default)
viewport_x = 0  # Current x position of the viewport
viewport_y = 0  # Current y position of the viewport

# Cached image data
current_surface = None
current_img_width = 0  # Width of original image
current_img_height = 0  # Height of original image
tiled_img_width = 0  # Width of tiled image
tiled_img_height = 0  # Height of tiled image

def load_image(image_path, target_width=None, target_height=None):
    """Load and scale image, create tiled surface with horizontal flip and vertical repeat."""
    if target_height is None:
        target_height = display_size[1]
    print(f"Loading image: {image_path}")
    try:
        img = Image.open(image_path)
        img_width, img_height = img.size
        aspect_ratio = target_height / img_height
        new_width = int(img_width * aspect_ratio)
        img = img.resize((new_width, target_height), Image.Resampling.BILINEAR)
        
        # Create horizontally flipped image
        flipped_h_img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        
        # Create horizontal tile (original + flipped)
        horizontal_tile = Image.new('RGB', (new_width * 2, target_height))
        horizontal_tile.paste(img, (0, 0))
        horizontal_tile.paste(flipped_h_img, (new_width, 0))
        
        # Create vertical tile (horizontal_tile + horizontal_tile)
        tiled_img = Image.new('RGB', (new_width * 2, target_height * 2))
        tiled_img.paste(horizontal_tile, (0, 0))
        tiled_img.paste(horizontal_tile, (0, target_height))
        
        # Save to temporary BMP file (Pygame on Raspbian prefers BMP)
        with tempfile.NamedTemporaryFile(suffix='.bmp', delete=False) as tmp_file:
            tiled_img.save(tmp_file.name, format='BMP')
            surface = pygame.image.load(tmp_file.name)
            tmp_file.close()
            os.unlink(tmp_file.name)  # Delete temporary file
        
        print(f"Loaded surface: {image_path}, orig_w={new_width}, orig_h={target_height}, tiled_w={new_width * 2}, tiled_h={target_height * 2}")
        return surface, new_width, target_height, new_width * 2, target_height * 2
    except Exception as e:
        print(f"Error loading image {image_path}: {e}")
        return None, 0, 0, 0, 0

def draw_viewport(screen, surface):
    """Draw the wrapped viewport of the surface to the screen."""
    global viewport_x, viewport_y, tiled_img_width, tiled_img_height
    if surface is None:
        return
    
    tiled_w = surface.get_width()
    tiled_h = surface.get_height()
    src_x = viewport_x % tiled_w
    src_y = viewport_y % tiled_h
    screen_w, screen_h = display_size[0], display_size[1]
    
    # Blit with wrapping in both directions
    dest_y = 0
    rem_h = screen_h
    cur_src_y = src_y
    while rem_h > 0:
        fit_y = tiled_h - cur_src_y
        blit_h = min(rem_h, fit_y)
        
        dest_x = 0
        rem_w = screen_w
        cur_src_x = src_x
        while rem_w > 0:
            fit_x = tiled_w - cur_src_x
            blit_w = min(rem_w, fit_x)
            src_rect = pygame.Rect(cur_src_x, cur_src_y, blit_w, blit_h)
            screen.blit(surface, (dest_x, dest_y), src_rect)
            rem_w -= blit_w
            dest_x += blit_w
            cur_src_x = 0
        
        rem_h -= blit_h
        dest_y += blit_h
        cur_src_y = 0

def print_screen(text):
    font = pygame.font.SysFont("arial", 36)  # Use Arial font with size 36
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    screen.fill(BLACK)
    text = font.render(text, True, WHITE)  # Text, antialiasing, color
    screen.blit(text, (100, 100))
    pygame.display.flip()
    
def display_image(index, viewport_x_param=0, viewport_y_param=0):
    """Display the image at the given index."""
    global current_surface, current_img_width, current_img_height, tiled_img_width, tiled_img_height, viewport_x, viewport_y, current_image_index
    viewport_x = viewport_x_param
    viewport_y = viewport_y_param
    current_image_index = index
    print(f"Displaying image: {image_files[index] if image_files else 'No image'}, viewport_x={viewport_x}, viewport_y={viewport_y}")
    if not image_files:
        screen.fill((0, 0, 0))  # Black screen if no images
        pygame.display.flip()
        return
    
    image_path = os.path.join(IMAGE_DIR, image_files[index])
    current_surface, current_img_width, current_img_height, tiled_img_width, tiled_img_height = load_image(image_path)
    
    if current_surface is None:
        print(f"Failed to load image {image_files[index]}, skipping...")
        screen.fill((0, 0, 0))
        pygame.display.flip()
        # Move to next image if available
        if len(image_files) > 1:
            next_index = (index + 1) % len(image_files)
            display_image(next_index)
        return
    
    # Create a black background
    screen.fill((0, 0, 0))
    
    # Draw the visible portion of the tiled image
    draw_viewport(screen, current_surface)
    
    pygame.display.flip()

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

@app.route('/select/<name>', methods=['GET'])
def select_image(name):
    """Queue a specific image by index to be displayed."""
    global current_image_index, panning_x, panning_y
    viewport_x_val = float(request.args.get('viewport_x', '0'))
    viewport_y_val = float(request.args.get('viewport_y', '0'))
    try:
        if name in image_files:
            panning_x = False  # Stop panning when selecting image
            panning_y = False
            current_image_index = image_files.index(name)
            display_queue.put(('image', (current_image_index, viewport_x_val, viewport_y_val)))
            return jsonify({"status": "success", "image": name, "index": current_image_index})
        return jsonify({"status": "error", "message": "No images available"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/pan/<direction>', methods=['GET'])
def pan_image(direction):
    """Start panning in the specified direction."""
    global panning_x, panning_y, pan_direction_x, pan_direction_y
    if not image_files:
        return jsonify({"status": "error", "message": "No images available"})
    
    dir_lower = direction.lower()
    if dir_lower == 'left':
        pan_direction_x = -1
        panning_x = True
    elif dir_lower == 'right':
        pan_direction_x = 1
        panning_x = True
    elif dir_lower == 'up':
        pan_direction_y = -1
        panning_y = True
    elif dir_lower == 'down':
        pan_direction_y = 1
        panning_y = True
    else:
        return jsonify({"status": "error", "message": "Invalid direction. Use 'left', 'right', 'up', or 'down'."})
    
    display_queue.put(('pan', None))  # Trigger display update
    return jsonify({"status": "success", "direction": direction})

@app.route('/viewport_x/<x>', methods=['GET'])
def set_viewport_x(x):
    global viewport_x
    viewport_x = float(x)
    print(f'Set viewport_x to {viewport_x}')
    return jsonify({"status": "success", "message": "viewport_x set"})

@app.route('/viewport_y/<y>', methods=['GET'])
def set_viewport_y(y):
    global viewport_y
    viewport_y = float(y)
    print(f'Set viewport_y to {viewport_y}')
    return jsonify({"status": "success", "message": "viewport_y set"})

@app.route('/print/<text>', methods=['GET'])
def text(text):
    print(f'print text {text}')
    display_queue.put(('print', text))
    return jsonify({"status": "success", "message": "Text queued"})

@app.route('/stop', methods=['GET'])
def stop_pan():
    """Stop panning."""
    global panning_x, panning_y
    panning_x = False
    panning_y = False
    display_queue.put(('stop', None))  # Queue stop command
    return jsonify({"status": "success", "message": "Panning and sound playback stopped"})

@app.route('/set_speed/<speed>', methods=['GET'])
def set_speed(speed):
    """Set the panning speed in pixels per second."""
    try:
        new_speed = float(speed)
        if new_speed <= 0:
            return jsonify({"status": "error", "message": "Speed must be positive."})
        if new_speed > 2000:
            return jsonify({"status": "error", "message": "Speed must not exceed 2000 pixels/second."})
        global pan_speed
        pan_speed = new_speed
        display_queue.put(('speed', new_speed))
        return jsonify({"status": "success", "speed": new_speed})
    except ValueError:
        return jsonify({"status": "error", "message": "Invalid speed. Must be a number."})

@app.route('/status', methods=['GET'])
def status():
    """Return current image and status."""
    if image_files:
        pan_dir_x_str = "left" if pan_direction_x == -1 else "right" if pan_direction_x == 1 else "stopped"
        pan_dir_y_str = "up" if pan_direction_y == -1 else "down" if pan_direction_y == 1 else "stopped"
        return jsonify({
            "status": "success",
            "current_image": image_files[current_image_index],
            "current_index": current_image_index,
            "total_images": len(image_files),
            "panning_x": panning_x,
            "pan_direction_x": pan_dir_x_str,
            "panning_y": panning_y,
            "pan_direction_y": pan_dir_y_str,
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
    global panning_x, panning_y, viewport_x, viewport_y, current_image_index, pan_direction_x, pan_direction_y, pan_speed
    print("Starting main loop")
    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Clear cached surface to ensure clean initialization
    global current_surface, current_img_width, current_img_height, tiled_img_width, tiled_img_height
    current_surface = None
    current_img_width = 0
    current_img_height = 0
    tiled_img_width = 0
    tiled_img_height = 0
    
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
                display_image(*data)
            elif command == 'pan':
                if current_surface:
                    screen.fill((0, 0, 0))
                    draw_viewport(screen, current_surface)
                    pygame.display.flip()
                    print(f"Panning update: viewport_x={viewport_x}, viewport_y={viewport_y}")
            elif command == 'speed':
                pan_speed = data
                print(f"Panning speed set to: {pan_speed} pixels/second")
            elif command == 'sound':
                filename, volume = data
                if not play_sound(filename, volume):
                    print(f"Failed to play sound: {filename}")
            elif command == 'stop':
                pygame.mixer.stop()  # Stop all sound playback
                panning_x = False
                panning_y = False
                print("Stopped panning and sound playback")
            elif command == 'print':
                print_screen(data)
        except queue.Empty:
            pass
        
        # Update panning
        update_needed = False
        if panning_x and image_files and current_surface:
            viewport_x += pan_direction_x * pan_speed * delta_time
            update_needed = True
        if panning_y and image_files and current_surface:
            viewport_y += pan_direction_y * pan_speed * delta_time
            update_needed = True
        
        if update_needed:
            screen.fill((0, 0, 0))
            draw_viewport(screen, current_surface)
            pygame.display.flip()
            print(f"Panning: viewport_x={viewport_x}, viewport_y={viewport_y}")
    
    pygame.quit()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pygame.quit()
