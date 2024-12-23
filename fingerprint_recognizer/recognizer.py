from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
import sys
import keyboard
from .image_locator import ImageLocator
from .overlay import RectangleOverlay
import os
from .utils.logger import log


class FingerprintRecognizer:
    def __init__(self, resources_path="\\resources", threshold=0.75, update_interval=500):
        """
        Initialize the Fingerprint Recognizer.
        
        :param resources_path: Path to the resources directory.
        :param threshold: Matching threshold for image detection.
        :param update_interval: Interval for overlay updates (in milliseconds).
        """
        self.app = QApplication(sys.argv)
        self.resources_path = os.path.dirname(__file__)+resources_path
        self.template_paths = self._get_main_templates()
        self.locator = ImageLocator(threshold=threshold)
        self.locator.template_paths = self.template_paths

        self.overlay = RectangleOverlay(text_position=(100, 100))
        self.update_interval = update_interval
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_overlay)

    def _get_main_templates(self):
        """
        Retrieve the main template image paths from the resources directory.
        
        :return: List of paths to main template images.
        """
        log("Loading main template images...", level="info")
        main_templates = []
        for file in sorted(os.listdir(self.resources_path)):
            file_path = os.path.join(self.resources_path, file)
            if os.path.isfile(file_path) and file.endswith(".png"):
                main_templates.append(file_path)
        log(f"Main templates loaded: {main_templates}", level="success")
        return main_templates

    def _get_sub_templates(self, base_name):
        """
        Retrieve sub-template image paths corresponding to a main template.
        
        :param base_name: Name of the main template (without extension).
        :return: List of paths to sub-template images.
        """
        sub_templates = []
        subfolder_path = os.path.join(self.resources_path, base_name)
        if os.path.isdir(subfolder_path):
            for file in sorted(os.listdir(subfolder_path)):
                file_path = os.path.join(subfolder_path, file)
                if os.path.isfile(file_path) and file.endswith(".png"):
                    sub_templates.append(file_path)
        log(f"Sub-templates loaded for {base_name}: {sub_templates}", level="info")
        return sub_templates

    def locate_on_screen(self):
        """Locate templates on the screen and update the overlay."""
        log("Starting on-screen template detection...", level="info")
        self.overlay.display_text("Taking screenshot")

        # Take a screenshot
        screenshot = self.locator.take_screenshot()
        log("Screenshot captured.", level="success")

        # Load main templates
        log(f"Loading main templates from paths: {self.template_paths}", level="info")
        self.locator.load_templates(self.template_paths)

        # Locate main templates
        main_locations = self.locator.locate_images_on_screen(screenshot=screenshot, only_once=True)
        log(f"Main template locations: {main_locations}", level="info")

        rectangles = []
        if main_locations:
            first_location = main_locations[0]
            rectangles.append(
                (first_location["x"], first_location["y"], first_location["width"], first_location["height"])
            )
            log(f"Main template found at: {first_location}", level="success")

            # Get sub-template paths
            base_name, _ = os.path.splitext(os.path.basename(first_location["path"]))
            sub_templates = self._get_sub_templates(base_name)

            # Load and locate sub-templates
            self.locator.load_templates(sub_templates)
            sub_locations = self.locator.locate_images_on_screen(screenshot, only_once=False)
            log(f"Sub-template locations: {sub_locations}", level="info")

            for location in sub_locations:
                rectangles.append(
                    (location["x"], location["y"], location["width"], location["height"])
                )
            self.overlay.display_text(f"Fragments found for {base_name}")
        else:
            self.overlay.display_text("No fingerprint found.")
            log("Main template not found.", level="error")

        # Update the overlay with the rectangles
        self.overlay.rectangles = rectangles
        log(f"Overlay updated with rectangles: {rectangles}", level="success")

    def clear_overlay(self):
        """Clear the overlay."""
        log("Clearing overlay rectangles...", level="warning")
        self.overlay.rectangles = []

    def update_overlay(self):
        """Check for key inputs and update overlay."""
        log("Waiting for key input...", level="info")

        if keyboard.is_pressed("n"):
            log("Refreshing overlay...", level="success")
            self.locate_on_screen()
            self.overlay.update()

        if keyboard.is_pressed("x"):
            log("Clearing overlay...", level="error")
            self.clear_overlay()
            self.overlay.update()

    def start(self):
        """Start the application and overlay."""
        log("Application started. Press 'n' to locate and 'x' to clear.", level="info")
        self.timer.start(self.update_interval)
        self.overlay.show()
        sys.exit(self.app.exec_())


# Example usage:
if __name__ == "__main__":
    recognizer = FingerprintRecognizer(resources_path="resources")
    recognizer.start()
