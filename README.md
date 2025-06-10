# clipboard-citation-pickup
Written after losing track of numerous references when preparing slides.
A light app that listens to clipboard events and picks up copied citations for easy management.
## Dependencies
```bash
pip install PyQt6 openai
```

Or no openAI if not interested in informative previews; just delete import.
## Usage
1. Entry point: `citationCollector.py`
1. Copy a text that matches criteria (coded in `CitationManager.isPubmedCitation`). For now it's just designed for what you will copy when clicking "Cite" button in pubmed article page.
2. A small window will appear and you may optionally add notes to it.
3. Put random notes about this citation, then click "Save w/ notes" and it will appeear in the list of main window.
4. Or, if notes are not needed, ignore the window and it adds the citation itself after timeout.
