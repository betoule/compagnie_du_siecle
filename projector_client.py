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
                url = f"{self.url}/select/{param[0]}"
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
            else:
                print(f"Error: Invalid projector action: {action} {param or ''}")
                return

            response = requests.get(url, timeout=5)
            response.raise_for_status()
            print(f"Sent: {url}, Response: {response.json()}")
        except requests.RequestException as e:
            print(f"Error: Failed to send command to {url}: {e}")

class LedService(Service):
    def execute(self, action, *args):
        """Send an HTTP request to the LEDs server."""
        if args:
            param = args[0]
        if len(args) > 1:
            color = args[1]
        if len(args) > 2:
            delay = args[2]
        if action == 'all' and param and len(param) == 6:
            url = f"{self.url}/all?color={param}"
        elif action == 'set' and param and '-' in param:
            url = f"{self.url}/set?leds={param}&color={color}"
            if delay:
                url += f"&delay={delay}"
        else:
            print(f"Error: Invalid LEDs action: {action} {param or ''}")
            return

        response = requests.get(url, timeout=5)
        response.raise_for_status()
        print(f"Sent: {url}, Response: {response.json()}")

comp_types = {'Led': LedService,
              'Projector': ProjectorService}

class ProjectorClient:
    def __init__(self, config_file):
        self.components = {}
        self.scenes = []
        self.current_scene_index = 0
        self.running = True
        self.load_config(config_file)
        self.key_listener = None

    def load_config(self, config_file):
        """Parse the configuration file to extract server URL and scenes."""
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
                    current_scene = {'name': scene_name, 'commands': []}
                    self.scenes.append(current_scene)
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
                current_scene['commands'].append(line)

        if not self.components:
            print("Error: No 'component=' line found in config file.")
            sys.exit(1)
        if not self.scenes:
            print("Error: No scenes defined in config file.")
            sys.exit(1)

        print(f"Loaded config: components={self.components}, Scenes={len(self.scenes)}")

    def execute_command(self, command):
        """Execute a single command."""
        parts = command.split()
        if not parts:
            return

        if parts[0] == 'wait':
            if len(parts) == 1:
                print("Waiting for Enter key...")
                input()  # Wait for user input (Enter)
            elif len(parts) == 2:
                try:
                    seconds = float(parts[1])
                    print(f"Waiting for {seconds} seconds...")
                    time.sleep(seconds)
                except ValueError:
                    print(f"Error: Invalid wait duration: {parts[1]}")
        elif parts[0] in self.components:
            try:
                print(f"Executing {command}")
                self.components[parts[0]].execute(*parts[1:])
            except Exception as e:
                print(e)
            if len(parts) < 2:
                print(f"Error: Invalid projector command: {command}")
                return
        else:
            print(f"Error: Unknown command: {command}")

    def execute_scene(self, index):
        """Execute all commands in the specified scene."""
        if 0 <= index < len(self.scenes):
            self.current_scene_index = index
            scene = self.scenes[index]
            print(f"\nExecuting scene: {scene['name']} (index {index})")
            for command in scene['commands']:
                if not self.running:
                    break
                self.execute_command(command)
        else:
            print(f"Error: Invalid scene index: {index}")

    def on_key_press(self, key):
        """Handle key presses for scene navigation."""
        try:
            if key == keyboard.Key.left:
                if self.current_scene_index > 0:
                    print("Switching to previous scene")
                    self.execute_scene(self.current_scene_index - 1)
            elif key == keyboard.Key.right:
                if self.current_scene_index < len(self.scenes) - 1:
                    print("Switching to next scene")
                    self.execute_scene(self.current_scene_index + 1)
            elif key == keyboard.Key.esc:
                print("Exiting...")
                self.running = False
                sys.exit(0)
        except Exception as e:
            print(f"Error handling key press: {e}")

    def start(self):
        """Start the client and key listener."""
        # Execute the first scene
        if self.scenes:
            self.execute_scene(0)

        # Start key listener in a separate thread
        listener = keyboard.Listener(on_press=self.on_key_press)
        listener.start()
        print("\nListening for arrow keys: Left=Previous scene, Right=Next scene, Esc=Exit")

        # Keep the main thread alive
        try:
            while self.running:
                time.sleep(0.1)
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
