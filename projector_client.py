import requests
import time
import re
from pynput import keyboard
import sys
import threading

class Service():
    def __init__(self, name, url):
        self.name = name
        self.url = url

    def execute(self, action, *param):
        print(f"Received {action}, {param}")
        
class ProjectorService(Service):
    def execute(self, action, *param):
        """Send an HTTP request to the projector server."""
        try:
            if action == 'select' and param:
                if len(param) == 1:
                    param = (param[0], 0)
                url = f"{self.url}/select/{param[0]}?viewport={param[1]}"
            elif action == 'set_speed' and param:
                url = f"{self.url}/set_speed/{param[0]}"
            elif action == 'pan' and param[0] in ['left', 'right']:
                url = f"{self.url}/pan/{param[0]}"
            elif action == 'viewport' and param:
                url = f"{self.url}/viewport/{param[0]}"
            elif action == 'stop':
                url = f"{self.url}/stop"
            elif action == 'play_sound':
                url = f"{self.url}/play_sound/{param[0]}?volume={param[1]}"
            elif action == 'print':
                url = f"{self.url}/print/{'%20'.join(param)}"
            else:
                print(f"Error: Invalid projector action: {action} {param or ''}")
                return

            response = requests.get(url, timeout=5)
            response.raise_for_status()
            #print(f"Sent: {url}, Response: {response.json()}")
        except requests.RequestException as e:
            print(f"Error: Failed to send command to {url}: {e}")

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

class LedService(Service):
    MAX_BRIGHTNESS = 255

    def scale_color(self, hex_str):
        r,g,b = parse_hex_color(hex_str)
        if (r+g+b) > self.MAX_BRIGHTNESS:
            new_color = ''.join([f'{int(v/(r+g+b)*self.MAX_BRIGHTNESS):02x}' for v in (r, g, b)])
            print(f'Rescaled {hex_str} to {new_color} to match brightness limitation')
            return new_color
        else:
            return hex_str
        
    def execute(self, action, *args):
        """Send an HTTP request to the LEDs server."""
        if args:
            param = args[0]
        if len(args) > 1:
            color = args[1]
        if len(args) > 2:
            delay = args[2]
        if action == 'all' and param and len(param) == 6:
            url = f"{self.url}/all?color={self.scale_color(param)}"
        elif action == 'set' and param and '-' in param:
            url = f"{self.url}/set?leds={param}&color={self.scale_color(color)}"
            if delay:
                url += f"&delay={delay}"
        else:
            print(f"Error: Invalid LEDs action: {action} {param or ''}")
            return

        response = requests.get(url, timeout=5)
        response.raise_for_status()
        #print(f"Sent: {url}, Response: {response.json()}")

comp_types = {'Led': LedService,
              'Projector': ProjectorService}

inter_scene="""wait
led all 000000
projector stop
wait
led all 010101
projector print scene {scene}
wait
"""

class ProjectorClient:
    def __init__(self, config_file):
        self.config_file = config_file
        self.running = True
        self.load_config(config_file)
        self.key_listener = None
        self.status = 'Waiting'

    def add_command(self, line):
        self.commands.append(line)
        self.cursor = len(self.commands)

    def load_config(self, config_file):
        """Parse the configuration file to extract server URL and scenes."""
        self.components = {}
        self.commands = []
        self.scenes = []
        self.cursor = 0
        try:
            with open(config_file, 'r') as f:
                lines = f.readlines()
        except FileNotFoundError:
            print(f"Error: Config file '{config_file}' not found.")
            sys.exit(1)

        current_scene = None
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):  # Skip empty lines and comments
                if line.startswith('# scene'):  # New scene
                    scene_name = line[7:].strip()  # Extract scene name
                    current_scene = {'name': scene_name, 'cursor': self.cursor}
                    self.scenes.append(current_scene)
                    for command in inter_scene.splitlines():
                        self.add_command(command.format(scene=scene_name))
                continue

            if line.startswith('component'):
                _, name, comp_type, url = line.split(' ')
                name = name.strip()
                url = f"http://{url.strip()}"
                if name in self.components:
                    print(f"Error: Multiple '{name=}' lines found.")
                    sys.exit(1)
                self.components[name] = comp_types[comp_type](name, url)
                continue
            
            # Parse commands
            if current_scene is not None:
                self.add_command(line)
        if not self.components:
            print("Error: No 'component=' line found in config file.")
            sys.exit(1)
        if not self.scenes:
            print("Error: No scenes defined in config file.")
            sys.exit(1)

        print(f"Loaded config: components={self.components}, Scenes={len(self.scenes)}, Commands={len(self.commands)}")
        for scene in self.scenes:
            print(f'{scene["name"]}: {scene["cursor"]}')
        self.cursor = 0
        
    def execute_command(self, command):
        """Execute a single command."""
        parts = command.split()
        if not parts:
            return

        if parts[0] == 'wait':
            if len(parts) == 1:
                self.status = 'Waiting'
                print("Waiting for key stroke...")
            elif len(parts) == 2:
                try:
                    seconds = float(parts[1])
                    print(f"Waiting for {seconds} seconds...")
                    time.sleep(seconds)
                except ValueError:
                    print(f"Error: Invalid wait duration: {parts[1]}")
        elif parts[0] in self.components:
            try:
                print(f"(scene {self.get_current_scene()}, {self.cursor}): Executing {command}")
                self.components[parts[0]].execute(*parts[1:])
            except Exception as e:
                print(e)
            if len(parts) < 2:
                print(f"Error: Invalid projector command: {command}")
        else:
            print(f"Error: Unknown command: {command}")
        self.cursor += 1

    def execution_loop(self):
        while self.running:
            if self.status == 'Waiting':
                time.sleep(0.1)
                continue
            if self.cursor < len(self.commands):
                self.execute_command(self.commands[self.cursor])
            else:
                print('Fin du script')
                self.execute_command('wait')

    def get_current_scene(self):
        for index, scene in enumerate(self.scenes):
            if scene['cursor'] > self.cursor:
                return index - 1
        return len(self.scenes)

    def execute_scene(self, delta):
        """Execute all commands in the specified scene."""
        index = self.get_current_scene() + delta
        if 0 <= index < len(self.scenes):
            scene = self.scenes[index]
            self.cursor = scene['cursor']
            print(f"\nExecuting scene: {scene['name']} (index {index}, cursor {self.cursor})")
            self.status = 'Running'
        else:
            print(f"Error: Invalid scene index: {index}")

    def on_key_press(self, key):
        """Handle key presses for scene navigation."""
        try:
            if key == keyboard.Key.up:
                print("Switching to previous scene")
                self.execute_scene(- 1)
            elif key == keyboard.Key.down:
                print("Switching to next scene")
                self.execute_scene(+1)
            elif key == keyboard.Key.left:
                self.cursor -= 2
                index = self.get_current_scene()
                print(f"\Back to scene: {self.scenes[index]['name']} (index {index}, cursor {self.cursor})")
                self.execute_command('wait')
            elif key == keyboard.Key.right:
                self.cursor += 1
                self.execute_command('wait')                
            elif key == keyboard.Key.esc:
                print("Exiting...")
                self.running = False
                sys.exit(0)
            elif key == keyboard.Key.space:
                self.status = 'Running'
            elif key == keyboard.KeyCode.from_char('r'):
                self.load_config(self.config_file)
        except Exception as e:
            print(f"Error handling key press: {e}")

    def start(self):
        """Start the client and key listener."""
        # Start key listener in a separate thread
        listener = keyboard.Listener(on_press=self.on_key_press)
        listener.start()
        print("\nListening for arrow keys: Left=Previous scene, Right=Next scene, Esc=Exit")

        # Keep the main thread alive
        try:
            self.execution_loop()
        except KeyboardInterrupt:
            self.running = False
        finally:
            listener.stop()

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 projector_client.py <config_file>")
        sys.exit(1)
    
    client = ProjectorClient(sys.argv[1])
    client.start()

if __name__ == "__main__":
    main()
