import sys, re
from typing import Optional

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
    QWidget, QListWidget, QListWidgetItem, QPushButton,
    QLabel, QTextEdit, QSplitter, QMessageBox,
    QDialog, QComboBox
)
from PyQt6.QtCore import QTimer, pyqtSignal, Qt, pyqtSignal
from PyQt6.QtGui import QFont

from citation import Citation, CitationManager
from export import exportCitations
from listener import ClipboardListener
from qkNoteDlg import QuickNoteDialog

class CitationWindow(QMainWindow):
    """main app window"""
    
    citationAdded = pyqtSignal(str)
    
    def __init__(self) -> None:
        super().__init__()
        self.citation_manager = CitationManager()
        self.clipboard_listener = ClipboardListener()
        self.setupUi()
        self.connectSignals()

        self.loadExistingCitations()

        self.clipboard_listener.start()
    
    def setupUi(self) -> None:
        self.setWindowTitle("PubMed Citation Collector")
        self.setGeometry(100, 100, 800, 400)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # main layout
        layout = QVBoxLayout(central_widget)
        
        # header with library selector
        header_layout = QHBoxLayout()
        
        header = QLabel("📋 PubMed Citation Collector")
        header.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header_layout.addWidget(header)
        
        header_layout.addStretch()

        # library selector
        library_layout = QHBoxLayout()
        library_label = QLabel("Library:")
        library_label.setStyleSheet("font-weight: bold;")
        self.library_combo = QComboBox()
        self.library_combo.setMinimumWidth(120)
        self.updateLibraryList()
        
        library_layout.addWidget(library_label)
        library_layout.addWidget(self.library_combo)
        
        header_layout.addLayout(library_layout)
        layout.addLayout(header_layout)
        
        # status label
        self.status_label = QLabel("Monitoring clipboard... Copy a PubMed citation!")
        self.status_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.status_label)
        
        # splitter for list and preview
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # citations list
        self.citation_list = QListWidget()
        self.citation_list.setMaximumWidth(450)
        splitter.addWidget(self.citation_list)
        
        # preview panel
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        
        preview_label = QLabel("Citation Preview:")
        preview_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        preview_layout.addWidget(preview_label)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setPlaceholderText("Select a citation to preview...")
        preview_layout.addWidget(self.preview_text)
        
        splitter.addWidget(preview_widget)
        
        # buttons
        button_layout = QHBoxLayout()
        
        self.remove_btn = QPushButton("Remove Selected")
        self.remove_btn.setEnabled(False)
        button_layout.addWidget(self.remove_btn)
        
        self.clear_btn = QPushButton("Clear All")
        button_layout.addWidget(self.clear_btn)

        # add test button for easier debugging
        test_btn = QPushButton("🧪 Test Note Dialog")
        test_btn.clicked.connect(self.testNoteDialog)
        button_layout.addWidget(test_btn)

        # export btn
        self.export_btn = QPushButton("📤 Export")
        button_layout.addWidget(self.export_btn)
        
        button_layout.addStretch()
        
        count_label = QLabel("Citations: ")
        self.count_display = QLabel("0")
        self.count_display.setStyleSheet("font-weight: bold; color: #2196F3;")
        button_layout.addWidget(count_label)
        button_layout.addWidget(self.count_display)
        
        layout.addLayout(button_layout)
    
    def connectSignals(self) -> None:
        self.clipboard_listener.newTextDetected.connect(self.onNewClipboardText)
        self.citation_list.itemClicked.connect(self.onCitationSelected)
        self.remove_btn.clicked.connect(self.removeCitation)
        self.clear_btn.clicked.connect(self.clearCitations)    
        self.export_btn.clicked.connect(lambda: exportCitations(self, self.citation_manager.citations))
        self.library_combo.currentTextChanged.connect(self.onLibraryChanged)

        QTimer.singleShot(100, self.checkForSummaryUpdates)
    
    def testNoteDialog(self) -> None:
        """tests the note dialog manually"""
        test_citation = "Zuchero JB, Barres BA. Intrinsic and extrinsic control of oligodendrocyte development. Curr Opin Neurobiol. 2013 Dec;23(6):914-20. PMID: 23831087"
        dialog = QuickNoteDialog(test_citation, self)
        result = dialog.exec()
        print(f"Dialog result: {result}, Notes: '{dialog.notes}'")
        
    def onNewClipboardText(self, text: str) -> None:
        """handles new clipboard text"""
        print(f"Processing clipboard text: {text[:100]}...")
        try:
            if self.citation_manager.isPubmedCitation(text):
                print("Citation detected!")
                
                dialog = QuickNoteDialog(text, self)
                result = dialog.exec()
                
                if result == QDialog.DialogCode.Accepted:
                    add_result = self.citation_manager.addCitation(text, dialog.notes)
                    
                    if add_result == True:
                        # new citation added
                        new_citation = self.citation_manager.citations[-1]
                        self.addCitationToList(new_citation, len(self.citation_manager.citations) - 1)
                        note_status = " with note" if dialog.notes else ""
                        self.updateStatus(f"✅ Citation saved{note_status}!")
                        
                    elif add_result == "note_appended":
                        # note was appended to existing citation
                        self.refreshCitationList()  # refresh to show updated note indicator
                        self.updateStatus(f"📝 Note appended to existing citation!")
                        
                    else:
                        # duplicate with no new note
                        self.updateStatus(f"⚠️ Citation already exists")
            else:
                print("Not detected as citation")
        except Exception as e:
            print(f"Error processing clipboard: {e}")

    def addCitationToList(self, citation: Citation, index: Optional[int] = None) -> None:
        """adds citation to the display list"""
        # use summary if available, otherwise fallback to text preview
        if citation.summary:
            display_text = citation.summary
        else:
            display_text = citation.text[:60] + "..." if len(citation.text) > 60 else citation.text
        
        pmid_text = f" [PMID: {citation.pmid}]" if citation.pmid else ""
        note_indicator = " 📝" if citation.notes else ""
        
        item_text = f"{citation.timestamp.strftime('%H:%M')}: {display_text}{pmid_text}{note_indicator}"
        
        item = QListWidgetItem(item_text)
        
        # use provided index or calculate it
        if index is not None:
            item.setData(Qt.ItemDataRole.UserRole, index)
        else:
            item.setData(Qt.ItemDataRole.UserRole, len(self.citation_manager.citations) - 1)
        
        # add subtle styling
        if citation.summary:
            item.setToolTip(f"AI Summary: {citation.summary}\n\nFull text: {citation.text[:200]}...")
        else:
            item.setToolTip(f"Full text: {citation.text[:200]}...")
        
        self.citation_list.addItem(item)
        
        # only update count if we're not in a batch refresh
        if index is None:
            self.updateCount()
    
    def checkForSummaryUpdates(self) -> None:
        """periodically checks if summaries have been updated"""
        # check if any citation got a new summary
        needs_refresh = False
        for i, citation in enumerate(self.citation_manager.citations):
            if i < self.citation_list.count():
                item = self.citation_list.item(i)
                current_text = item.text()
                
                # check if the display should show summary but currently shows truncated text
                if citation.summary and not citation.summary in current_text:
                    needs_refresh = True
                    break
            else:
                # list is shorter than citations, definitely need refresh
                needs_refresh = True
                break
        
        if needs_refresh:
            print("Refreshing citation list due to new summaries")
            self.refreshCitationList()
        
        # schedule next check
        QTimer.singleShot(2000, self.checkForSummaryUpdates)

    def refreshCitationList(self) -> None:
        """rebuilds the citation list with correct indices"""
        # remember current selection
        current_row = self.citation_list.currentRow()
        
        self.citation_list.clear()
        for i, citation in enumerate(self.citation_manager.citations):
            self.addCitationToList(citation, i)  # pass correct index
        
        # restore selection if possible
        if 0 <= current_row < self.citation_list.count():
            self.citation_list.setCurrentRow(current_row)
        
        self.updateCount()
    
    def onCitationSelected(self, item: QListWidgetItem) -> None:
        """handles citation selection"""
        index = item.data(Qt.ItemDataRole.UserRole)
        if 0 <= index < len(self.citation_manager.citations):
            citation: Citation = self.citation_manager.citations[index]
            
            # format preview with notes
            preview_text = citation.text
            if citation.notes:
                # format multiple notes nicely
                formatted_notes = citation.notes.replace('\n---\n', '\n💭 Additional Note:\n')
                preview_text += f"\n\n💭 Notes:\n{formatted_notes}"
            
            self.preview_text.setPlainText(preview_text)
            self.remove_btn.setEnabled(True)
    
    def removeCitation(self) -> None:
        """removes selected citation"""
        current_row = self.citation_list.currentRow()
        if current_row >= 0:
            item = self.citation_list.item(current_row)
            index = item.data(Qt.ItemDataRole.UserRole)
            
            self.citation_manager.removeCitation(index)
            self.citation_list.takeItem(current_row)
            
            # update indices for remaining items
            for i in range(self.citation_list.count()):
                list_item = self.citation_list.item(i)
                old_index = list_item.data(Qt.ItemDataRole.UserRole)
                if old_index > index:
                    list_item.setData(Qt.ItemDataRole.UserRole, old_index - 1)
            
            self.preview_text.clear()
            self.remove_btn.setEnabled(False)
            self.updateCount()
            self.updateStatus("Citation removed")
    
    def clearCitations(self) -> None:
        """clears all citations after confirmation"""
        if self.citation_manager.citations:
            reply = QMessageBox.question(
                self, "Clear All", "Remove all citations?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.citation_manager.clearAll()
                self.citation_list.clear()
                self.preview_text.clear()
                self.remove_btn.setEnabled(False)
                self.updateCount()
                self.updateStatus("All citations cleared")

    def loadExistingCitations(self) -> None:
        """loads previously saved citations into the UI"""
        for i, citation in enumerate(self.citation_manager.citations):
            self.addCitationToList(citation, i)  # pass the correct index
        
        if self.citation_manager.citations:
            self.updateStatus(f"Loaded {len(self.citation_manager.citations)} saved citations")

        self.updateCount()

    def updateCount(self) -> None:
        """updates citation count display"""
        self.count_display.setText(str(len(self.citation_manager.citations)))
    
    def updateStatus(self, message: str) -> None:
        """updates status message"""
        self.status_label.setText(message)
        QTimer.singleShot(3000, lambda: self.status_label.setText("Monitoring clipboard..."))
    
    def updateLibraryList(self) -> None:
        """updates the library dropdown with available libraries"""
        current_library = self.citation_manager.library_name
        
        self.library_combo.clear()
        libraries = self.citation_manager.getAvailableLibraries()
        
        # add new library option
        libraries.append("+ New Library")
        
        self.library_combo.addItems(libraries)
        
        # set current library
        if current_library in libraries:
            self.library_combo.setCurrentText(current_library)
    
    def onLibraryChanged(self, library_name: str) -> None:
        """handles library selection change"""
        if library_name == "+ New Library":
            self.createNewLibrary()
        elif library_name != self.citation_manager.library_name:
            self.switchToLibrary(library_name)
    
    def createNewLibrary(self) -> None:
        """creates a new library"""
        from PyQt6.QtWidgets import QInputDialog
        
        name, ok = QInputDialog.getText(
            self, "New Library", 
            "Enter library name:",
            text="research_project"
        )
        
        if ok and name.strip():
            # sanitize name
            clean_name = re.sub(r'[^\w\-_]', '_', name.strip())
            self.switchToLibrary(clean_name)
        else:
            # restore previous selection
            self.library_combo.setCurrentText(self.citation_manager.library_name)
    
    def switchToLibrary(self, library_name: str) -> None:
        """switches to the specified library"""
        if library_name == self.citation_manager.library_name:
            return
        
        # switch library
        self.citation_manager.switchLibrary(library_name)
        
        # update UI
        self.citation_list.clear()
        self.preview_text.clear()
        self.remove_btn.setEnabled(False)
        
        # reload citations for new library
        self.loadExistingCitations()
        
        # update library list and window title
        self.updateLibraryList()
        self.setWindowTitle(f"PubMed Citation Collector - {library_name}")
        self.updateStatus(f"Switched to library: {library_name}")

    def closeEvent(self, event) -> None:
        """cleanup on window close"""
        self.clipboard_listener.stop()
        event.accept()


def main() -> None:
    """application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("PubMed Citation Collector")
    
    window = CitationWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()