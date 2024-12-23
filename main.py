import argparse
from textual.app import App, ComposeResult
from textual.widgets import Button, Label, Footer, Header, Static
from textual.containers import Vertical, Horizontal
from fingerprint_recognizer import FingerprintRecognizer

class RecognizerTUI(App):
    """A Textual TUI for the Fingerprint Recognizer."""
    
    CSS_PATH = "tui_styles.css"  # Optional CSS for styling
    BINDINGS = [
        ("n", "refresh", "Refresh Overlay"),
        ("x", "clear", "Clear Overlay"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self, *args, headless=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.headless = headless
        self.recognizer = FingerprintRecognizer()
        self.recognizer_running = False

    def compose(self) -> ComposeResult:
        """Compose the UI layout."""
        if self.headless:
            return []  # Don't compose any UI if running in headless mode
        
        yield Header()
        yield Vertical(
            Label("Fingerprint Recognizer TUI", id="title"),
            Static("Press 'n' to refresh the overlay, 'x' to clear, and 'q' to quit."),
            Horizontal(
                Button("Start Recognizer", id="start_btn"),
                Button("Stop Recognizer", id="stop_btn", disabled=True),
                Button("Quit", id="quit_btn"),
                id="controls",
            ),
            id="main",
        )
        yield Footer()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id
        if button_id == "start_btn":
            self.start_recognizer()
        elif button_id == "stop_btn":
            self.stop_recognizer()
        elif button_id == "quit_btn":
            self.exit()

    def action_refresh(self) -> None:
        """Refresh the overlay."""
        try:
            if self.recognizer_running:
                self.recognizer.locate_on_screen()
        except Exception as e:
            self.exit()
            print(e)

    def action_clear(self) -> None:
        """Clear the overlay."""
        if self.recognizer_running:
            self.recognizer.clear_overlay()

    def start_recognizer(self):
        """Start the recognizer application."""
        if not self.recognizer_running:
            self.recognizer_running = True
            self.recognizer.start()
            self.query_one("#start_btn").disabled = True
            self.query_one("#stop_btn").disabled = False
            self.query_one(Static).update("Recognizer started!")

    def stop_recognizer(self):
        """Stop the recognizer application."""
        if self.recognizer_running:
            self.recognizer_running = False
            self.recognizer.timer.stop()
            self.recognizer.overlay.hide()
            self.query_one("#start_btn").disabled = False
            self.query_one("#stop_btn").disabled = True
            self.query_one(Static).update("Recognizer stopped!")

    def action_quit(self) -> None:
        """Quit the TUI application."""
        self.stop_recognizer()
        self.exit()

    def run_headless(self):
        """Run the recognizer without TUI (headless mode)."""
        self.start_recognizer()
        try:
            while self.recognizer_running:
                # In headless mode, you can add custom logic for processing here.
                pass  # Simulate the ongoing recognition process.
        except KeyboardInterrupt:
            self.stop_recognizer()


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Run the Fingerprint Recognizer TUI.")
    parser.add_argument(
        "--headless", action="store_true", help="Run the recognizer in headless mode without the TUI."
    )
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()

    if args.headless:
        app = RecognizerTUI(headless=True)
        app.run_headless()  # Run without the TUI
    else:
        RecognizerTUI().run()  # Run with the TUI interface
