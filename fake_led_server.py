import os
import pygame
from flask import Flask, jsonify, request
import threading
import queue
import time
import re

# Flask app
app = Flask(__name__)

# LED strip settings
NUM_LEDS = 300  # 5m strip with 60 LEDs/m
LED_WIDTH = 6  # Pixel width per LED in display
STRIP_HEIGHT = 50  # Height of the strip display
WINDOW_WIDTH = NUM_LEDS * LED_WIDTH
WINDOW_HEIGHT = STRIP_HEIGHT + 20  # Extra space for title

# LED state (list of RGB tuples)
led_colors = [(0, 0, 0) for _ in range(NUM_LEDS)]

# Queue for display updates
display_queue = queue.Queue()

# Pygame display thread
def pygame_thread():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption('Fake LED Strip')
    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Process updates from queue
        try:
            command, data = display_queue.get_nowait()
            if command == 'update':
                start, end, color_rgb, delay = data
                if delay > 0:
                    # Sweeping effect
                    for i in range(start, end + 1):
                        led_colors[i] = color_rgb
                        draw_strip(screen)
                        pygame.display.flip()
                        time.sleep(delay)
                else:
                    # Set range at once
                    for i in range(start, end + 1):
                        led_colors[i] = color_rgb
                    draw_strip(screen)
                    pygame.display.flip()
            elif command == 'all':
                color_rgb = data
                for i in range(NUM_LEDS):
                    led_colors[i] = color_rgb
                draw_strip(screen)
                pygame.display.flip()
        except queue.Empty:
            pass

        clock.tick(30)

    pygame.quit()

def draw_strip(screen):
    """Draw the LED strip on the screen."""
    screen.fill((0, 0, 0))  # Black background
    for i in range(NUM_LEDS):
        r, g, b = led_colors[i]
        pygame.draw.rect(screen, (r, g, b), (i * LED_WIDTH, 0, LED_WIDTH, STRIP_HEIGHT))
    pygame.draw.rect(screen, (255, 255, 255), (0, 0, WINDOW_WIDTH, STRIP_HEIGHT), 1)  # Border

def parse_hex_color(hex_str):
    """Parse 6-digit hex color to RGB tuple."""
    if len(hex_str) != 6:
        return None
    try:
        r = int(hex_str[0:2], 16)
        g = int(hex_str[2:4], 16)
        b = int(hex_str[4:6], 16)
        return (r, g, b)
    except ValueError:
        return None

def parse_led_range(range_str):
    """Parse 'start-end' to (start, end)."""
    match = re.match(r'^(\d+)-(\d+)$', range_str)
    if not match:
        return None
    start = int(match.group(1))
    end = int(match.group(2))
    if start < 0 or end >= NUM_LEDS or start > end:
        return None
    return (start, end)

@app.route('/all', methods=['GET'])
def set_all():
    hex_color = request.args.get('color')
    if not hex_color:
        return jsonify({"status": "error", "message": "Missing 'color' parameter"}), 400
    color_rgb = parse_hex_color(hex_color)
    if color_rgb is None:
        return jsonify({"status": "error", "message": "Invalid hex color (use RRGGBB)"}), 400
    display_queue.put(('all', color_rgb))
    return jsonify({"status": "success", "color": hex_color}), 200

@app.route('/set', methods=['GET'])
def set_range():
    leds_range = request.args.get('leds')
    hex_color = request.args.get('color')
    delay_str = request.args.get('delay', '0')
    if not leds_range or not hex_color:
        return jsonify({"status": "error", "message": "Missing 'leds' or 'color' parameter"}), 400
    range_tuple = parse_led_range(leds_range)
    if range_tuple is None:
        return jsonify({"status": "error", "message": "Invalid LED range (use start-end, 0 to 299)"}), 400
    start, end = range_tuple
    color_rgb = parse_hex_color(hex_color)
    if color_rgb is None:
        return jsonify({"status": "error", "message": "Invalid hex color (use RRGGBB)"}), 400
    try:
        delay = float(delay_str)
        if delay < 0:
            return jsonify({"status": "error", "message": "Invalid delay (use positive number or 0)"}), 400
    except ValueError:
        return jsonify({"status": "error", "message": "Invalid delay (use number)"}), 400
    display_queue.put(('update', (start, end, color_rgb, delay)))
    response = {"status": "success", "leds": leds_range, "color": hex_color, "delay": delay}
    return jsonify(response), 200

@app.route('/status', methods=['GET'])
def status():
    colors = [f"{r:02X}{g:02X}{b:02X}" for r, g, b in led_colors]
    return jsonify({"status": "success", "num_leds": NUM_LEDS, "colors": colors}), 200

def run_flask():
    app.run(host='0.0.0.0', port=8080, threaded=True)  # Port 8080 to avoid conflict with projector server

if __name__ == '__main__':
    # Start Pygame thread
    pygame_t = threading.Thread(target=pygame_thread, daemon=True)
    pygame_t.start()

    # Start Flask in main thread
    run_flask()