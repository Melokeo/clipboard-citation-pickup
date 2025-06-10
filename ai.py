import json
from pathlib import Path
from openai import OpenAI

def loadApiKey(
    config_path: Path = Path(__file__).parent / "cfg" / "openai_key.json"
) -> str:
    """loads openai api key from config file"""
    try:
        return json.loads(config_path.read_text())["api_key"]
    except Exception as e:
        print(f"Error loading API key: {e}")
        return ""

class OpenAIHelper:
    """handles openai requests for citation summarization"""
    
    def __init__(self) -> None:
        try:
            api_key = loadApiKey()
            if api_key:
                self.client = OpenAI(api_key=api_key)
                self.enabled = True
            else:
                self.client = None
                self.enabled = False
                print("OpenAI disabled - no API key found")
        except Exception as e:
            print(f"OpenAI initialization failed: {e}") 
            self.client = None
            self.enabled = False
    
    def generateCitationSummaries(self, citations: list[str]) -> dict[str, str]:
        """generates short summaries for citations"""
        if not self.enabled or not citations:
            return {}
        
        try:
            system_prompt = (
                "You are a citation summarizer. For each academic citation, extract the first author's last name "
                "and create a summary phrase with less than 5 words of the main topic. Format: 'LastName: Topic Summary'\n"
                "Scientific terms can use their established abbreviations, eg. Oligodendrocyte => OL, Oligodendrocyte progenitor cell => OPC"
                ""
                "Examples:\n"
                "- 'Smith et al. Neural networks in visual cortex...' -> 'Smith: NN in visual cortex'\n"
                "- 'Johnson AB, Lee C. CRISPR gene editing...' -> 'Johnson: CRISPR Editing'\n"
                "- 'Brown M. Synaptic plasticity mechanisms...' -> 'Brown: Synaptic Plasticity Mech.'\n"
                "- 'Sim FJ. CD140a identifies a population of highly myelinogenic, migration-competent and"
                " efficiently engrafting human oligodendrocyte progenitor cells' -> 'Sim: Engrafting OPC CD140a subpopulation'\n"
                "chondroitin sulfate proteoglycans -> CSPG. You may search the web for best scientific abbrs,"
                " especially those gene, protein and cell names."
                "Keep summaries short and informative, maximizing the distinguishability."
            )
            
            # batch citations for efficiency
            batched_prompt = "Summarize each citation, be sure to maximize the distinguishability.:\n\n" + \
                           "\n".join(f"{i+1}. {citation[:200]}" for i, citation in enumerate(citations))
            
            resp = self.client.chat.completions.create(
                model="gpt-4o-mini",  # using mini for cost efficiency
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": batched_prompt}
                ],
                temperature=0.3,
                max_tokens=800,
            )
            
            # parse response back to dict
            response_text = resp.choices[0].message.content.strip()
            summaries = {}
            
            lines = response_text.split('\n')
            for i, line in enumerate(lines):
                if line.strip() and i < len(citations):
                    # remove numbering if present
                    clean_line = line.strip()
                    if clean_line.startswith(f"{i+1}."):
                        clean_line = clean_line[len(f"{i+1}."):].strip()
                    summaries[citations[i]] = clean_line
            
            return summaries
            
        except Exception as e:
            print(f"OpenAI request failed: {e}")
            return {}
