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
        prompt = prompts.SEMANTIC_MEMORY_PROMPT.format(script=script)
        
        try:
            result = self.llm.generate_json(
                prompt=prompt,
                system_message="You are an expert at extracting semantic information. Return only valid JSON."
            )
            return result
        except Exception as e:
            # Return default structure if extraction fails
            return {
                "facts": [f"Error extracting semantic memory: {str(e)}"],
                "concepts": [],
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
        prompt = prompts.EPISODIC_MEMORY_PROMPT.format(script=script)
        
        try:
            result = self.llm.generate_json(
                prompt=prompt,
                system_message="You are an expert at extracting episodic information. Return only valid JSON."
            )
            return result
        except Exception as e:
            # Return default structure if extraction fails
            return {
                "scenes": [],
                "timeline": [f"Error extracting episodic memory: {str(e)}"],
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
        prompt = prompts.PROCEDURAL_MEMORY_PROMPT.format(script=script)
        
        try:
            result = self.llm.generate_json(
                prompt=prompt,
                system_message="You are an expert at extracting procedural information. Return only valid JSON."
            )
            return result
        except Exception as e:
            # Return default structure if extraction fails
            return {
                "skills_demonstrated": [f"Error extracting procedural memory: {str(e)}"],
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
