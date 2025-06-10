from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal

class ClipboardListener(QObject):
    """handles clipboard monitoring using signals"""
    
    newTextDetected = pyqtSignal(str)
    
    def __init__(self) -> None:
        super().__init__()
        self.clipboard = QApplication.clipboard()
        self.last_text = ""
        self.is_monitoring = False
    
    def start(self) -> None:
        """starts monitoring clipboard"""
        if not self.is_monitoring:
            self.clipboard.dataChanged.connect(self.onClipboardChanged)
            self.last_text = self.clipboard.text()
            self.is_monitoring = True
            print("Clipboard monitoring started")
    
    def stop(self) -> None:
        """stops monitoring"""
        if self.is_monitoring:
            self.clipboard.dataChanged.disconnect(self.onClipboardChanged)
            self.is_monitoring = False
            print("Clipboard monitoring stopped")
    
    def onClipboardChanged(self) -> None:
        """called when clipboard content changes"""
        try:
            current_text = self.clipboard.text()
            if current_text and current_text != self.last_text:
                print(f"Clipboard changed: {current_text[:50]}...")
                self.last_text = current_text
                self.newTextDetected.emit(current_text)
        except Exception as e:
            print(f"Clipboard error: {e}")
