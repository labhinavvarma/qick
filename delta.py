"""
Memory Extractor Module
Extracts semantic, episodic, and procedural memories from movie scripts
"""

import json
from typing import Dict, Any
from llm_client import SFAssistClient
import prompts


class MemoryExtractor:
    """Extracts different types of memories from movie scripts"""
    
    def __init__(self, llm_client: SFAssistClient):
        self.llm = llm_client
    
    def extract_semantic_memory(self, script: str) -> Dict[str, Any]:
        """
        Extract semantic memory from movie script
        
        Args:
            script: The movie script text
        
        Returns:
            Dictionary containing semantic memory
        """
        # Limit script length to avoid token issues
        script_preview = script[:8000] if len(script) > 8000 else script
        
        prompt = prompts.SEMANTIC_MEMORY_PROMPT.format(script=script_preview)
        
        try:
            result = self.llm.generate_json(
                prompt=prompt,
                system_message="Extract semantic memory as valid JSON. Return only JSON, nothing else."
            )
            
            # Validate required fields
            if not isinstance(result, dict):
                raise ValueError("Result is not a dictionary")
            
            # Ensure all required fields exist
            result.setdefault("facts", [])
            result.setdefault("concepts", [])
            result.setdefault("character_traits", {})
            result.setdefault("world_building", [])
            
            return result
            
        except Exception as e:
            print(f"Error in semantic memory extraction: {str(e)}")
            # Return default structure with error info
            return {
                "facts": [f"Extraction failed: {str(e)[:200]}"],
                "concepts": ["Error during extraction"],
                "character_traits": {},
                "world_building": []
            }
    
    def extract_episodic_memory(self, script: str) -> Dict[str, Any]:
        """
        Extract episodic memory from movie script
        
        Args:
            script: The movie script text
        
        Returns:
            Dictionary containing episodic memory
        """
        # Limit script length to avoid token issues
        script_preview = script[:8000] if len(script) > 8000 else script
        
        prompt = prompts.EPISODIC_MEMORY_PROMPT.format(script=script_preview)
        
        try:
            result = self.llm.generate_json(
                prompt=prompt,
                system_message="Extract episodic memory as valid JSON. Return only JSON, nothing else."
            )
            
            # Validate required fields
            if not isinstance(result, dict):
                raise ValueError("Result is not a dictionary")
            
            # Ensure all required fields exist
            result.setdefault("scenes", [])
            result.setdefault("timeline", [])
            result.setdefault("key_moments", [])
            result.setdefault("plot_points", [])
            
            return result
            
        except Exception as e:
            print(f"Error in episodic memory extraction: {str(e)}")
            # Return default structure with error info
            return {
                "scenes": [],
                "timeline": [f"Extraction failed: {str(e)[:200]}"],
                "key_moments": [],
                "plot_points": []
            }
    
    def extract_procedural_memory(self, script: str) -> Dict[str, Any]:
        """
        Extract procedural memory from movie script
        
        Args:
            script: The movie script text
        
        Returns:
            Dictionary containing procedural memory
        """
        # Limit script length to avoid token issues
        script_preview = script[:8000] if len(script) > 8000 else script
        
        prompt = prompts.PROCEDURAL_MEMORY_PROMPT.format(script=script_preview)
        
        try:
            result = self.llm.generate_json(
                prompt=prompt,
                system_message="Extract procedural memory as valid JSON. Return only JSON, nothing else."
            )
            
            # Validate required fields
            if not isinstance(result, dict):
                raise ValueError("Result is not a dictionary")
            
            # Ensure all required fields exist
            result.setdefault("skills_demonstrated", [])
            result.setdefault("processes", [])
            result.setdefault("rules_and_protocols", [])
            
            return result
            
        except Exception as e:
            print(f"Error in procedural memory extraction: {str(e)}")
            # Return default structure with error info
            return {
                "skills_demonstrated": [f"Extraction failed: {str(e)[:200]}"],
                "processes": [],
                "rules_and_protocols": []
            }
    
    def extract_all_memories(self, script: str, progress_callback=None) -> Dict[str, Any]:
        """
        Extract all three types of memories from movie script
        
        Args:
            script: The movie script text
            progress_callback: Optional callback function to report progress
        
        Returns:
            Dictionary containing all memories
        """
        memories = {
            "semantic_memory": {},
            "episodic_memory": {},
            "procedural_memory": {}
        }
        
        # Extract semantic memory
        if progress_callback:
            progress_callback("Extracting semantic memory...", 33)
        memories["semantic_memory"] = self.extract_semantic_memory(script)
        
        # Extract episodic memory
        if progress_callback:
            progress_callback("Extracting episodic memory...", 66)
        memories["episodic_memory"] = self.extract_episodic_memory(script)
        
        # Extract procedural memory
        if progress_callback:
            progress_callback("Extracting procedural memory...", 100)
        memories["procedural_memory"] = self.extract_procedural_memory(script)
        
        return memories
    
    def save_memories_to_json(self, memories: Dict[str, Any], filename: str) -> str:
        """
        Save memories to a JSON file
        
        Args:
            memories: The memories dictionary
            filename: Output filename
        
        Returns:
            Path to the saved file
        """
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(memories, f, indent=2, ensure_ascii=False)
        
        return filename
    
    def load_memories_from_json(self, filename: str) -> Dict[str, Any]:
        """
        Load memories from a JSON file
        
        Args:
            filename: Input filename
        
        Returns:
            Memories dictionary
        """
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
