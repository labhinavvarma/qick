"""
Memory Extractor Module
Extracts semantic, episodic, and procedural memories from movie scripts
Supports chunking for large scripts with multiple LLM calls
"""

import json
from typing import Dict, Any, List
from llm_client import SFAssistClient
import prompts


class MemoryExtractor:
    """Extracts different types of memories from movie scripts"""
    
    def __init__(self, llm_client: SFAssistClient):
        self.llm = llm_client
        self.chunk_size = 6000  # Characters per chunk
        self.chunk_overlap = 500  # Overlap between chunks for context
    
    def split_script_into_chunks(self, script: str) -> List[str]:
        """
        Split a large script into overlapping chunks
        
        Args:
            script: The movie script text
        
        Returns:
            List of script chunks
        """
        if len(script) <= self.chunk_size:
            return [script]
        
        chunks = []
        start = 0
        
        while start < len(script):
            end = start + self.chunk_size
            
            # If not the last chunk, try to break at a newline
            if end < len(script):
                # Look for a newline near the end of the chunk
                newline_pos = script.rfind('\n', end - 200, end)
                if newline_pos > start:
                    end = newline_pos
            
            chunks.append(script[start:end])
            
            # Move start position with overlap
            start = end - self.chunk_overlap
            
            # Prevent infinite loop
            if start >= len(script):
                break
        
        return chunks
    
    def merge_semantic_memories(self, memories_list: List[Dict]) -> Dict[str, Any]:
        """
        Merge multiple semantic memory extractions
        
        Args:
            memories_list: List of semantic memory dictionaries
        
        Returns:
            Merged semantic memory dictionary
        """
        merged = {
            "facts": [],
            "concepts": [],
            "character_traits": {},
            "world_building": []
        }
        
        for mem in memories_list:
            # Merge facts (deduplicate)
            for fact in mem.get("facts", []):
                if fact not in merged["facts"]:
                    merged["facts"].append(fact)
            
            # Merge concepts (deduplicate)
            for concept in mem.get("concepts", []):
                if concept not in merged["concepts"]:
                    merged["concepts"].append(concept)
            
            # Merge character traits
            for char, traits in mem.get("character_traits", {}).items():
                if char not in merged["character_traits"]:
                    merged["character_traits"][char] = []
                for trait in traits:
                    if trait not in merged["character_traits"][char]:
                        merged["character_traits"][char].append(trait)
            
            # Merge world building (deduplicate)
            for wb in mem.get("world_building", []):
                if wb not in merged["world_building"]:
                    merged["world_building"].append(wb)
        
        return merged
    
    def merge_episodic_memories(self, memories_list: List[Dict]) -> Dict[str, Any]:
        """
        Merge multiple episodic memory extractions
        
        Args:
            memories_list: List of episodic memory dictionaries
        
        Returns:
            Merged episodic memory dictionary
        """
        merged = {
            "scenes": [],
            "timeline": [],
            "key_moments": [],
            "plot_points": []
        }
        
        for mem in memories_list:
            # Merge scenes
            for scene in mem.get("scenes", []):
                merged["scenes"].append(scene)
            
            # Merge timeline (keep order)
            for event in mem.get("timeline", []):
                if event not in merged["timeline"]:
                    merged["timeline"].append(event)
            
            # Merge key moments
            for moment in mem.get("key_moments", []):
                if moment not in merged["key_moments"]:
                    merged["key_moments"].append(moment)
            
            # Merge plot points
            for point in mem.get("plot_points", []):
                if point not in merged["plot_points"]:
                    merged["plot_points"].append(point)
        
        return merged
    
    def merge_procedural_memories(self, memories_list: List[Dict]) -> Dict[str, Any]:
        """
        Merge multiple procedural memory extractions
        
        Args:
            memories_list: List of procedural memory dictionaries
        
        Returns:
            Merged procedural memory dictionary
        """
        merged = {
            "skills_demonstrated": [],
            "processes": [],
            "rules_and_protocols": []
        }
        
        for mem in memories_list:
            # Merge skills (deduplicate)
            for skill in mem.get("skills_demonstrated", []):
                if skill not in merged["skills_demonstrated"]:
                    merged["skills_demonstrated"].append(skill)
            
            # Merge processes
            for process in mem.get("processes", []):
                if process not in merged["processes"]:
                    merged["processes"].append(process)
            
            # Merge rules (deduplicate)
            for rule in mem.get("rules_and_protocols", []):
                if rule not in merged["rules_and_protocols"]:
                    merged["rules_and_protocols"].append(rule)
        
        return merged
    
    def extract_semantic_memory(self, script: str) -> Dict[str, Any]:
        """
        Extract semantic memory from movie script
        Handles large scripts by chunking
        
        Args:
            script: The movie script text
        
        Returns:
            Dictionary containing semantic memory
        """
        chunks = self.split_script_into_chunks(script)
        
        print(f"Processing semantic memory in {len(chunks)} chunk(s)...")
        
        all_memories = []
        
        for i, chunk in enumerate(chunks):
            print(f"  Chunk {i+1}/{len(chunks)}...")
            
            prompt = prompts.SEMANTIC_MEMORY_PROMPT.format(script=chunk)
            
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
                
                all_memories.append(result)
                
            except Exception as e:
                print(f"  Error in chunk {i+1}: {str(e)[:100]}")
                # Add partial result
                all_memories.append({
                    "facts": [f"Chunk {i+1} extraction failed"],
                    "concepts": [],
                    "character_traits": {},
                    "world_building": []
                })
        
        # Merge all chunks
        merged = self.merge_semantic_memories(all_memories)
        
        if not merged["facts"] or all("failed" in str(f).lower() for f in merged["facts"]):
            merged["facts"] = ["Extraction completed with errors - check individual chunks"]
        
        return merged
    
    def extract_episodic_memory(self, script: str) -> Dict[str, Any]:
        """
        Extract episodic memory from movie script
        Handles large scripts by chunking
        
        Args:
            script: The movie script text
        
        Returns:
            Dictionary containing episodic memory
        """
        chunks = self.split_script_into_chunks(script)
        
        print(f"Processing episodic memory in {len(chunks)} chunk(s)...")
        
        all_memories = []
        
        for i, chunk in enumerate(chunks):
            print(f"  Chunk {i+1}/{len(chunks)}...")
            
            prompt = prompts.EPISODIC_MEMORY_PROMPT.format(script=chunk)
            
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
                
                all_memories.append(result)
                
            except Exception as e:
                print(f"  Error in chunk {i+1}: {str(e)[:100]}")
                # Add partial result
                all_memories.append({
                    "scenes": [],
                    "timeline": [f"Chunk {i+1} extraction failed"],
                    "key_moments": [],
                    "plot_points": []
                })
        
        # Merge all chunks
        merged = self.merge_episodic_memories(all_memories)
        
        if not merged["timeline"] or all("failed" in str(t).lower() for t in merged["timeline"]):
            merged["timeline"] = ["Extraction completed with errors - check individual chunks"]
        
        return merged
    
    def extract_procedural_memory(self, script: str) -> Dict[str, Any]:
        """
        Extract procedural memory from movie script
        Handles large scripts by chunking
        
        Args:
            script: The movie script text
        
        Returns:
            Dictionary containing procedural memory
        """
        chunks = self.split_script_into_chunks(script)
        
        print(f"Processing procedural memory in {len(chunks)} chunk(s)...")
        
        all_memories = []
        
        for i, chunk in enumerate(chunks):
            print(f"  Chunk {i+1}/{len(chunks)}...")
            
            prompt = prompts.PROCEDURAL_MEMORY_PROMPT.format(script=chunk)
            
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
                
                all_memories.append(result)
                
            except Exception as e:
                print(f"  Error in chunk {i+1}: {str(e)[:100]}")
                # Add partial result
                all_memories.append({
                    "skills_demonstrated": [f"Chunk {i+1} extraction failed"],
                    "processes": [],
                    "rules_and_protocols": []
                })
        
        # Merge all chunks
        merged = self.merge_procedural_memories(all_memories)
        
        if not merged["skills_demonstrated"] or all("failed" in str(s).lower() for s in merged["skills_demonstrated"]):
            merged["skills_demonstrated"] = ["Extraction completed with errors - check individual chunks"]
        
        return merged
    
    def extract_all_memories(self, script: str, progress_callback=None) -> Dict[str, Any]:
        """
        Extract all three types of memories from movie script
        Handles large scripts by chunking
        
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
        
        # Calculate total chunks
        chunks = self.split_script_into_chunks(script)
        total_chunks = len(chunks) * 3  # 3 memory types
        current_chunk = 0
        
        # Extract semantic memory
        if progress_callback:
            progress_callback(f"Extracting semantic memory ({len(chunks)} chunks)...", 10)
        
        memories["semantic_memory"] = self.extract_semantic_memory(script)
        current_chunk += len(chunks)
        
        # Extract episodic memory
        if progress_callback:
            progress_callback(f"Extracting episodic memory ({len(chunks)} chunks)...", 40)
        
        memories["episodic_memory"] = self.extract_episodic_memory(script)
        current_chunk += len(chunks)
        
        # Extract procedural memory
        if progress_callback:
            progress_callback(f"Extracting procedural memory ({len(chunks)} chunks)...", 70)
        
        memories["procedural_memory"] = self.extract_procedural_memory(script)
        
        if progress_callback:
            progress_callback("Finalizing extraction...", 100)
        
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
