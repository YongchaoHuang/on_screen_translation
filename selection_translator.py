import sys
import numpy as np
import requests
import mss
import re
from PyQt6.QtWidgets import (
    QApplication, 
    QMainWindow, 
    QWidget, 
    QRubberBand, 
    QTextEdit, 
    QVBoxLayout
)
from PyQt6.QtCore import Qt, QPoint, QRect, QSize
from PyQt6.QtGui import QColor
import easyocr
import os

# Configuration
source_lang = "EN"
target_lang = "ZH"

DEEPL_API = "https://api-free.deepl.com/v2/translate" # use DEEPL_API = "https://api.deepl.com/v2/translate" if you are using a paid Deepl.com account
DEEPL_KEY = "YOUR_DEEPL_API_KEY"  # Replace with your key
MODEL_DIR = os.path.expanduser('~/.EasyOCR/model')
BULLET_PATTERN = re.compile(r'^(\s*[\•\-\*›»]|\s*\d+[\.\)]\s*)(.*)', re.UNICODE)

class RegionSelector(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Select Text Region (Drag Mouse)")
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        self.setGeometry(0, 0, 
                       QApplication.primaryScreen().size().width(),
                       QApplication.primaryScreen().size().height())
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.start_point = QPoint()
        self.rubber_band = QRubberBand(QRubberBand.Shape.Rectangle, self)
        self.selected_region = None

    def mousePressEvent(self, event):
        self.start_point = event.position().toPoint()
        self.rubber_band.setGeometry(QRect(self.start_point, QSize()))
        self.rubber_band.show()

    def mouseMoveEvent(self, event):
        self.rubber_band.setGeometry(QRect(self.start_point, 
                                         event.position().toPoint()).normalized())

    def mouseReleaseEvent(self, event):
        x1 = min(self.start_point.x(), event.position().toPoint().x())
        y1 = min(self.start_point.y(), event.position().toPoint().y())
        x2 = max(self.start_point.x(), event.position().toPoint().x())
        y2 = max(self.start_point.y(), event.position().toPoint().y())
        
        if abs(x2 - x1) < 10 or abs(y2 - y1) < 10:
            self.selected_region = None
        else:
            self.selected_region = (x1, y1, x2, y2)
        self.close()

def process_translation(content):
    try:
        response = requests.post(
            DEEPL_API,
            data={
                "auth_key": DEEPL_KEY,
                "text": content,
                "source_lang": source_lang,
                "target_lang": target_lang,
                "preserve_formatting": "1",
                "tag_handling": "xml"
            },
            timeout=5
        )
        return response.json()['translations'][0]['text']
    except Exception as e:
        print(f"Translation error: {str(e)}")
        return "[Translation Error]"

def get_translated_text(region):
    left, top, right, bottom = region
    width = right - left
    height = bottom - top
    
    if width <= 0 or height <= 0:
        return "Invalid region selected"

    with mss.mss() as sct:
        monitor = {"top": top, "left": left, "width": width, "height": height}
        try:
            img = sct.grab(monitor)
            img_np = np.frombuffer(img.rgb, dtype=np.uint8)
            img_np = img_np.reshape((img.height, img.width, 3))
        except Exception as e:
            return f"Capture error: {str(e)}"

    try:
        reader = easyocr.Reader(['en'], model_storage_directory=MODEL_DIR)
        results = reader.readtext(img_np, paragraph=False, detail=1)
        
        # Sort by vertical then horizontal position
        sorted_results = sorted(results, key=lambda x: (x[0][0][1], x[0][0][0]))
        
        translated_lines = []
        previous_bottom = 0
        line_gap_threshold = 10  # Pixels between lines
        
        for i, entry in enumerate(sorted_results):
            text = entry[1]
            bbox = entry[0]
            current_top = bbox[0][1]
            
            # Add paragraph spacing
            if i > 0 and (current_top - previous_bottom) > line_gap_threshold:
                translated_lines.append("")
            
            # Detect and preserve bullets/numbers
            match = BULLET_PATTERN.match(text)
            if match:
                bullet = match.group(1).strip()
                content = match.group(2).strip()
                prefix = f"{bullet} " if bullet else ""
            else:
                prefix = ""
                content = text

            if content:
                translated = process_translation(content)
                translated_lines.append(f"{prefix}{translated}")
            elif prefix:
                translated_lines.append(prefix)
            
            previous_bottom = bbox[-1][1]

        return "\n".join(translated_lines) if translated_lines else "No text detected"
    
    except Exception as e:
        return f"Processing error: {str(e)}"

class ResultWindow(QMainWindow):
    def __init__(self, text):
        super().__init__()
        self.setWindowTitle("Translated Text")
        self.setGeometry(100, 100, 800, 600)
        
        text_edit = QTextEdit()
        text_edit.setPlainText(text)
        text_edit.setReadOnly(True)
        text_edit.setStyleSheet("""
            QTextEdit {
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
                line-height: 1.6;
                padding: 15px;
            }
            """)
        
        layout = QVBoxLayout()
        layout.addWidget(text_edit)
        
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    selector = RegionSelector()
    selector.show()
    app.exec()
    
    if selector.selected_region:
        translated_text = get_translated_text(selector.selected_region)
        result_window = ResultWindow(translated_text)
        result_window.show()
    
    sys.exit(app.exec())
