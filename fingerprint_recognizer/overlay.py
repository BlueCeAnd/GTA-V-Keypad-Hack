import sys
from PyQt5.QtCore import Qt, QRect, QPoint
from PyQt5.QtGui import QColor, QPainter, QBrush, QPen, QFont
from PyQt5.QtWidgets import QApplication, QMainWindow, QDesktopWidget, QWidget


class RectangleOverlay(QWidget):
    def __init__(self, rectangles=None, color=(0, 255, 0), thickness=2, text=None, text_position=(0, 0)):
        super().__init__()
        self.rectangles = rectangles if rectangles else []
        self.color = QColor(*color)
        self.thickness = thickness
        self.text = text  # Text to be displayed
        self.text_position = text_position  # Position to display the text (x, y)

        # Set up the overlay window
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

        # Resize to full screen
        screen = QDesktopWidget().screenGeometry()
        self.setGeometry(0, 0, screen.width(), screen.height())

    def set_rectangles(self, rectangles):
        """
        Update the list of rectangles to be drawn.
        :param rectangles: List of rectangles [(x, y, width, height), ...]
        """
        self.rectangles = rectangles
        self.update()  # Trigger a repaint

    def display_text(self, text, position=None):
        """
        Set the text to be displayed on the overlay.
        :param text: Text to display
        :param position: (x, y) position of the text on the overlay
        """
        self.text = text
        if position is not None:
            self.text_position = position
            
        self.update()  # Trigger a repaint

    def paintEvent(self, event):
        """
        Draw the rectangles and text on the overlay.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        pen = QPen(self.color)
        pen.setWidth(self.thickness)
        painter.setPen(pen)

        # Draw the rectangles
        for rect in self.rectangles:
            x, y, width, height = rect
            painter.drawRect(QRect(x, y, width, height))

        # Draw the text if specified
        if self.text:
            painter.setPen(QPen(QColor(255, 255, 255)))  # White color for text
            painter.setFont(QFont("Arial", 24))  # Set font and size
            painter.drawText(QPoint(self.text_position[0], self.text_position[1]), self.text)

        painter.end()


# Example usage
def main():
    app = QApplication(sys.argv)

    # Example rectangles: (x, y, width, height)
    example_rectangles = [
        (100, 100, 200, 150),
        (400, 300, 100, 200),
        (600, 100, 150, 150),
    ]

    overlay = RectangleOverlay(rectangles=example_rectangles, color=(255, 0, 0), thickness=3)
    
    # Display some text on the overlay
    overlay.display_text("Sample Text", position=(100, 50))

    overlay.show()

    print("Overlay is active. Close the overlay window to exit.")
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()