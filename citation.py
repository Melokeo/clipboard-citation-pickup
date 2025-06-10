from datetime import datetime
from dataclasses import dataclass
from typing import Optional
import re, json

from pathlib import Path

from ai import OpenAIHelper

@dataclass
class Citation:
    """stores a pubmed citation with metadata"""
    text: str
    timestamp: datetime
    pmid: Optional[str] = None
    notes: str = ""  
    summary: str = ""

class CitationManager:
    """manages citation collection and validation"""
    
    def __init__(self, library_name: str = "default") -> None:
        self.library_name = library_name
        self.citations: list[Citation] = []
        self.data_file = Path.home() / f".pubmed_citations_{library_name}.json"
        self.openai_helper = OpenAIHelper()
        self.loadCitations()

    def switchLibrary(self, library_name: str) -> None:
        """switches to a different library"""
        # save current library first
        self.saveCitations()
        
        # switch to new library
        self.library_name = library_name
        self.data_file = Path.home() / f".pubmed_citations_{library_name}.json"
        self.citations.clear()
        self.loadCitations()
    
    def getAvailableLibraries(self) -> list[str]:
        """returns list of existing libraries"""
        home = Path.home()
        library_files = home.glob(".pubmed_citations_*.json")
        libraries = []
        
        for file in library_files:
            # extract library name from filename
            name = file.stem.replace(".pubmed_citations_", "")
            libraries.append(name)
        
        # always include default if not found
        if "default" not in libraries:
            libraries.append("default")
        
        return sorted(libraries)
    
    def isPubmedCitation(self, text: str) -> bool:
        """
        checks if text looks like a pubmed citation.\n
        modify to adapt for other formats.
        """
        text = text.strip()
        if len(text) < 20:
            return False
        
        # skip obvious code/programming content
        code_indicators = [
            'def ', 'import ', 'class ', 'return ', 'if __name__',
            'from typing', 'PyQt', 'QApplication', 'print(', '"""'
        ]
        if any(indicator in text for indicator in code_indicators):
            print("Skipping - detected as code")
            return False
        
        # must have actual citation structure, not just keywords
        has_pmid = bool(re.search(r'PMID:\s*\d+', text))
        has_doi = bool(re.search(r'doi:\s*10\.\d+', text))  # real DOI format
        has_journal_format = bool(re.search(r'\d{4}[;\s][A-Za-z\s]+\d+\(\d+\):\d+', text))
        has_author_year = bool(re.search(r'^[A-Z][a-z]+\s+[A-Z]{1,3}[a-z]*.*\d{4}', text))
        
        # require at least 1 strong indicator
        strong_indicators = [has_pmid, has_doi, has_journal_format and has_author_year]
        weak_indicators = ['epub' in text.lower(), 'pmcid:' in text.lower()]
        
        result = sum(strong_indicators) >= 1 or sum(weak_indicators) >= 2
        
        print(f"Citation detection - PMID: {has_pmid}, DOI: {has_doi}, Journal: {has_journal_format}, Author: {has_author_year}, Result: {result}")
        return result
    
    def addCitation(self, text: str, notes: str = "") -> bool:
        """
        adds citation if valid, returns success status
        Returns:
        True if append citation list, False if not (duplicative);
        "note_appended" if duplicative but with new notes
        """
        if not self.isPubmedCitation(text):
            return False
        
        # extract PMID if present
        pmid_match = re.search(r'PMID:\s*(\d+)', text, re.IGNORECASE)
        pmid = pmid_match.group(1) if pmid_match else None
        
        # check for existing citation
        existing_citation = None
        for citation in self.citations:
            if citation.text == text.strip():
                existing_citation = citation
                break
        
        if existing_citation:
            # citation already exists - append note if new note provided
            if notes.strip():
                if existing_citation.notes:
                    # append with separator if existing notes exist
                    existing_citation.notes += f"\n---\n{notes.strip()}"
                else:
                    # first note for this citation
                    existing_citation.notes = notes.strip()
                
                self.saveCitations()  # save the updated notes
                print(f"Appended note to existing citation: {notes[:50]}...")
                return "note_appended" # not complying with function typing!!
            else:
                print("Citation already exists, no new note to append")
                return False
        else:
            # new citation - add it
            citation = Citation(
                text=text.strip(),
                timestamp=datetime.now(),
                pmid=pmid,
                notes=notes,
                summary="",
            )
            
            self.citations.append(citation)
            self.saveCitations()
            self.updateSummaries()
            return True
    
    def updateSummaries(self) -> None:
        """updates AI summaries for **all** citations"""
        if not self.openai_helper.enabled:
            return
        
        # find citations without summaries
        citations_needing_summary = [
            c.text for c in self.citations # if not c.summary
        ]
        
        if not citations_needing_summary:
            return
        
        print(f"Requesting summaries for {len(citations_needing_summary)} citations...")
        
        # get summaries from gpt
        summaries = self.openai_helper.generateCitationSummaries(citations_needing_summary)
        
        # update citations with summaries
        for citation in self.citations:
            if citation.text in summaries:
                citation.summary = summaries[citation.text]
        
        # save updated citations
        self.saveCitations()
        print(f"Updated {len(summaries)} citation summaries")
    
    def removeCitation(self, index: int) -> None:
        """removes citation at given index"""
        if 0 <= index < len(self.citations):
            del self.citations[index]
            self.saveCitations()  # auto-save after removing
    
    def clearAll(self) -> None:
        """removes all citations"""
        self.citations.clear()
        self.saveCitations()  # auto-save after clearing
    
    def saveCitations(self) -> None:
        """saves citations to disk"""
        try:
            # convert to serializable format
            data = []
            for citation in self.citations:
                data.append({
                    'text': citation.text,
                    'timestamp': citation.timestamp.isoformat(),
                    'pmid': citation.pmid,
                    'notes': citation.notes,
                    'summary': citation.summary  # include summary
                })
            
            # save json
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"Saved {len(self.citations)} citations to {self.data_file}")
            
        except Exception as e:
            print(f"Error saving citations: {e}")
    
    def loadCitations(self) -> None:
        """loads citations from disk"""
        try:
            if not self.data_file.exists():
                print("No saved citations found")
                return
            
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # back to Citation
            for item in data:
                citation = Citation(
                    text=item['text'],
                    timestamp=datetime.fromisoformat(item['timestamp']),
                    pmid=item.get('pmid'),
                    notes=item.get('notes', ''),
                    summary=item.get('summary', '')  # load summary
                )
                self.citations.append(citation)
            
            print(f"Loaded {len(self.citations)} citations from {self.data_file}")
        except KeyError as e:
            print(f'Wrong key in citation loading: {e}')
            self.citations = []
        except Exception as e:
            print(f"Error loading citations: {e}")
            self.citations = []
    
    def exportCitations(self, file_path: str) -> bool:
        """exports citations to a readable format"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("PubMed Citations Export\n")
                f.write("=" * 50 + "\n\n")
                
                for i, citation in enumerate(self.citations, 1):
                    f.write(f"Citation {i}:\n")
                    f.write(f"Added: {citation.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    if citation.pmid:
                        f.write(f"PMID: {citation.pmid}\n")
                    f.write(f"Text: {citation.text}\n")
                    if citation.notes:
                        f.write(f"Notes: {citation.notes}\n")
                    f.write("\n" + "-" * 80 + "\n\n")
            
            return True
        except Exception as e:
            print(f"Export error: {e}")
            return False
        