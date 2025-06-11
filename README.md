# clipboard-citation-pickup
Written after losing track of numerous references when preparing slides.

A light app that listens to clipboard events and picks up copied citations for easy management.

![image](https://github.com/user-attachments/assets/e9b2a8b6-2ff4-483a-96f7-cf70e8bc74af)

## Dependencies
Python >= 3.10

Tested on Windows but theoretically works in Linux.

```bash
pip install PyQt6 openai
```

Or no openAI if not interested in informative previews; just delete import.
## Usage
1. Entry point: `citationCollector.py`
1. Copy a text that matches criteria (coded in `CitationManager.isPubmedCitation`). For now it's just designed for what you will copy when clicking "Cite" button in pubmed article page.
2. A small window will appear and you may optionally add notes to it.
3. Put random notes about this citation, then click "Save w/ notes" and it will appeear in the list of main window.
4. Or, if no note is needed, ignore the window and it adds the citation itself after timeout.
5. Adding repetitive citations will only append current notes.

## Misc
- Supports multiple libraries for better organization
- Can batch export into txt file.
- Data itself is stored in `{user}/.pubmed_citations_{lib}.json`
- Qt seems like an overkill for this UI.
- With the help & misguidance of Claude AI.


