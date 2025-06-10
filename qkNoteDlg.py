from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QTextEdit, QDialog, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QWidget, QApplication
)
from PyQt6.QtGui import QKeyEvent

class SmartTextEdit(QTextEdit):
    """textEdit with custom enter behavior"""
    
    enterPressed = pyqtSignal()
    
    def keyPressEvent(self, event:QKeyEvent) -> None:
        """handles enter key behavior"""
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            if event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
                # shift+enter = new line (default behavior)
                super().keyPressEvent(event)
            else:
                # enter = save with note
                self.enterPressed.emit()
        else:
            super().keyPressEvent(event)

class QuickNoteDialog(QDialog):
    """compact expandable popup for quick note-taking"""
    
    def __init__(self, citation_preview: str, parent=None) -> None:
        super().__init__(parent)
        self.citation_preview = citation_preview
        self.notes = ""
        self.is_expanded = False
        self.drag_start_position = None  # for dragging
        
        self.setupCompactUi()
        
        # make it non-modal and less intrusive
        self.setWindowFlags(
            Qt.WindowType.Tool | 
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint
        )
        
        # auto-close timer
        self.auto_close_timer = QTimer()
        self.auto_close_timer.setSingleShot(True)
        self.auto_close_timer.timeout.connect(self.autoClose)
        self.auto_close_timer.start(5000)
        
        # countdown for visual feedback
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self.updateCountdown)
        self.countdown_timer.start(1000)
        self.remaining_seconds = 5
        
        self.positionBottomRight()
    
    def setupCompactUi(self) -> None:
        """sets up compact initial interface"""
        self.setFixedSize(280, 80)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        # compact header with drag handle
        header_layout = QHBoxLayout()
        
        # drag handle indicator
        drag_label = QLabel("⋮⋮")
        drag_label.setStyleSheet("color: #999; font-size: 8px;")
        drag_label.setFixedWidth(12)
        header_layout.addWidget(drag_label)
        
        icon_label = QLabel("📄")
        header_layout.addWidget(icon_label)
        
        # very short preview
        preview = self.citation_preview[:35] + "..." if len(self.citation_preview) > 35 else self.citation_preview
        self.preview_label = QLabel(preview)
        self.preview_label.setStyleSheet("font-size: 10px; color: #555;")
        self.preview_label.setWordWrap(True)
        header_layout.addWidget(self.preview_label, 1)
        
        # countdown
        self.countdown_label = QLabel("6s")
        self.countdown_label.setStyleSheet("color: #FF5722; font-size: 10px; font-weight: bold;")
        header_layout.addWidget(self.countdown_label)
        
        layout.addWidget(self.createHeaderWidget(header_layout))
        
        # compact buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(4)
        
        self.save_btn = QPushButton("✓ Save")
        self.save_btn.setFixedHeight(24)
        self.save_btn.setStyleSheet("QPushButton { background: #4CAF50; color: white; border: none; border-radius: 3px; font-size: 10px; }")
        
        self.note_btn = QPushButton("📝 Note")
        self.note_btn.setFixedHeight(24)
        self.note_btn.setStyleSheet("QPushButton { background: #2196F3; color: white; border: none; border-radius: 3px; font-size: 10px; }")
        
        self.skip_btn = QPushButton("✗")
        self.skip_btn.setFixedHeight(24)
        self.skip_btn.setFixedWidth(24)
        self.skip_btn.setStyleSheet("QPushButton { background: #757575; color: white; border: none; border-radius: 3px; font-size: 10px; }")
        
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.note_btn)
        button_layout.addWidget(self.skip_btn)
        
        layout.addLayout(button_layout)
        
        # connect signals
        self.save_btn.clicked.connect(self.saveNote)
        self.note_btn.clicked.connect(self.expandForNote)
        self.skip_btn.clicked.connect(self.skipNote)
        
        # initially no note input
        self.note_input = None
    
    def createHeaderWidget(self, layout) -> QWidget:
        """creates header widget for dragging"""
        header_widget = QWidget()
        header_widget.setLayout(layout)
        header_widget.setStyleSheet("QWidget:hover { background-color: #f0f0f0; }")
        return header_widget
    
    def expandForNote(self) -> None:
        """expands dialog to show note input"""
        if self.is_expanded:
            return
            
        self.is_expanded = True
        self.auto_close_timer.stop()
        
        # resize to expanded size
        self.setFixedSize(320, 180)
        
        # add note input section
        layout = self.layout()
        
        # fuller citation preview
        self.preview_label.setText(self.citation_preview[:90] + "..." if len(self.citation_preview) > 90 else self.citation_preview)
        
        # note input with custom text edit
        note_label = QLabel("💭 Quick note (Enter to save, Shift+Enter for new line):")
        note_label.setStyleSheet("font-size: 10px; color: #666; margin-top: 8px;")
        layout.addWidget(note_label)
        
        self.note_input = SmartTextEdit()  # custom text edit
        self.note_input.setPlaceholderText("Tags, thoughts, relevance...")
        self.note_input.setMaximumHeight(50)
        self.note_input.setStyleSheet("border: 1px solid #ddd; border-radius: 3px; font-size: 11px;")
        
        # connect custom enter handling
        self.note_input.enterPressed.connect(self.saveWithNote)
        
        layout.addWidget(self.note_input)
        
        # update buttons
        self.note_btn.setText("💾 Save w/ Note")
        self.note_btn.clicked.disconnect()
        self.note_btn.clicked.connect(self.saveWithNote)
        
        # focus input
        self.note_input.setFocus()
        
        # reposition if needed
        self.adjustPosition()
        
    def positionBottomRight(self) -> None:
        """positions dialog in bottom-right corner"""
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(
            screen.right() - self.width() - 20,
            screen.bottom() - self.height() - 60  # leave space for taskbar
        )
    
    def adjustPosition(self) -> None:
        """adjusts position after expansion to stay on screen"""
        screen = QApplication.primaryScreen().availableGeometry()
        current_pos = self.pos()
        
        # move up if expanded dialog goes below screen
        if current_pos.y() + self.height() > screen.bottom() - 60:
            new_y = screen.bottom() - self.height() - 60
            self.move(current_pos.x(), new_y)
    
    def updateCountdown(self) -> None:
        """updates countdown display"""
        self.remaining_seconds -= 1
        self.countdown_label.setText(f"{self.remaining_seconds}s")
        if self.remaining_seconds <= 0:
            self.countdown_timer.stop()
    
    def saveNote(self) -> None:
        """saves without note"""
        self.cleanup()
        self.accept()
    
    def saveWithNote(self) -> None:
        """saves with note from expanded input"""
        if self.note_input:
            self.notes = self.note_input.toPlainText().strip()
        self.cleanup()
        self.accept()
    
    def skipNote(self) -> None:
        """skips saving citation"""
        self.cleanup()
        self.reject()
    
    def autoClose(self) -> None:
        """auto-saves citation without note"""
        self.cleanup()
        self.accept()  # auto-save rather than skip
    
    def cleanup(self) -> None:
        """stops timers"""
        self.auto_close_timer.stop()
        self.countdown_timer.stop()
    
    def keyPressEvent(self, event) -> None:
        """handle keyboard shortcuts"""
        if event.key() == Qt.Key.Key_Escape:
            self.skipNote()
        elif (event.key() == Qt.Key.Key_Return and 
              event.modifiers() == Qt.KeyboardModifier.ControlModifier):
            if self.is_expanded:
                self.saveWithNote()
            else:
                self.saveNote()
        else:
            super().keyPressEvent(event)
    
        # mouse events for dragging
    def mousePressEvent(self, event) -> None:
        """starts drag operation"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.globalPosition().toPoint()
    
    def mouseMoveEvent(self, event) -> None:
        """handles dragging"""
        if (event.buttons() == Qt.MouseButton.LeftButton and 
            self.drag_start_position is not None):
            
            # calculate new position
            diff = event.globalPosition().toPoint() - self.drag_start_position
            new_pos = self.pos() + diff
            
            # keep window on screen
            screen = QApplication.primaryScreen().availableGeometry()
            new_pos.setX(max(0, min(new_pos.x(), screen.width() - self.width())))
            new_pos.setY(max(0, min(new_pos.y(), screen.height() - self.height())))
            
            self.move(new_pos)
            self.drag_start_position = event.globalPosition().toPoint()
    
    def mouseReleaseEvent(self, event) -> None:
        """ends drag operation"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = None
            