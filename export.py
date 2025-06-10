import re
from datetime import datetime
from PyQt6.QtWidgets import (
    QDialog, QLabel, QVBoxLayout,
    QCheckBox, QButtonGroup, QRadioButton,
    QMessageBox, QFileDialog
)

from citation import Citation

class ExportDialog(QDialog):
    """dialog for export options"""
    
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setupUi()
    
    def setupUi(self) -> None:
        """sets up the export options dialog"""
        self.setWindowTitle("Export Options")
        self.setFixedSize(280, 200)
        
        layout = QVBoxLayout(self)
        
        # sort options
        layout.addWidget(QLabel("Order:"))
        self.sort_group = QButtonGroup(self)
        self.sort_keep = QRadioButton("Keep current order")
        self.sort_time = QRadioButton("Sort by time (newest first)")
        self.sort_author = QRadioButton("Sort by author (A-Z)")
        self.sort_keep.setChecked(True)
        
        self.sort_group.addButton(self.sort_keep)
        self.sort_group.addButton(self.sort_time)
        self.sort_group.addButton(self.sort_author)
        
        layout.addWidget(self.sort_keep)
        layout.addWidget(self.sort_time)
        layout.addWidget(self.sort_author)
        
        # include options
        self.include_index = QCheckBox("Include index numbers")
        self.include_notes = QCheckBox("Include notes")
        self.include_index.setChecked(True)
        self.include_notes.setChecked(True)
        layout.addWidget(self.include_index)
        layout.addWidget(self.include_notes)
        
        # buttons
        from PyQt6.QtWidgets import QDialogButtonBox
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def getOptions(self) -> dict[str, bool]:
        """returns selected export options"""
        return {
            'sort_by_time': self.sort_time.isChecked(),
            'sort_by_author': self.sort_author.isChecked(),
            'include_index': self.include_index.isChecked(),
            'include_notes': self.include_notes.isChecked()
        }

def extractFirstAuthor(citation_text: str) -> str:
    """extracts first author last name for sorting"""
    # try to find author pattern at start of citation
    match = re.match(r'^([A-Z][a-z]+)', citation_text.strip())
    if match:
        return match.group(1).lower()
    
    # fallback - return first word
    first_word = citation_text.strip().split()[0] if citation_text.strip() else ""
    return re.sub(r'[^a-zA-Z]', '', first_word).lower()

def exportCitations(parent, citations: list[Citation]) -> None:
    if not citations:
        QMessageBox.information(parent, "Export", "No citations to export")
        return

    dialog = ExportDialog(parent)
    if dialog.exec() != QDialog.DialogCode.Accepted:
        return

    options = dialog.getOptions()

    file_path, _ = QFileDialog.getSaveFileName(
        parent, "Export Citations",
        f"citations_{datetime.now().strftime('%Y%m%d')}.txt",
        "Text Files (*.txt)"
    )

    if not file_path:
        return

    citations_copy = citations.copy()

    if options['sort_by_time']:
        citations_copy.sort(key=lambda c: c.timestamp, reverse=True)
    elif options['sort_by_author']:
        citations_copy.sort(key=lambda c: extractFirstAuthor(c.text))

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"Citations Export ({len(citations_copy)} total)\n")
            f.write("=" * 50 + "\n\n")
            for i, citation in enumerate(citations_copy, 1):
                line = citation.text
                if options['include_notes'] and citation.notes:
                    line += f" [note: {citation.notes}]"
                if options['include_index']:
                    f.write(f"{i}. {line}\n\n")
                else:
                    f.write(f"{line}\n\n")

        QMessageBox.information(parent, "Export", f"Exported to:\n{file_path}")

    except Exception as e:
        QMessageBox.warning(parent, "Export Error", f"Failed to export: {e}")