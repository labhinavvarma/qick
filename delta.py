"""
Chatbot Module
Answers questions about movies using extracted memories and script context
"""

import json
from typing import Dict, Any, List, Tuple
from llm_client import SFAssistClient
import prompts


class MovieChatbot:
    """Chatbot for answering questions about movies"""
    
    def __init__(self, llm_client: SFAssistClient):
        self.llm = llm_client
        self.script_context = ""
        self.memories = {}
        self.chat_history: List[Tuple[str, str]] = []
    
    def set_context(self, script: str, memories: Dict[str, Any]):
        """
        Set the context for the chatbot
        
        Args:
            script: The movie script (will be truncated if too long)
            memories: The extracted memories dictionary
        """
        # Store first 3000 characters of script as context
        self.script_context = script[:3000]
        self.memories = memories
    
    def ask(self, question: str) -> str:
        """
        Ask a question about the movie
        
        Args:
            question: User's question
        
        Returns:
            The chatbot's answer
        """
        if not self.memories:
            return "Please upload and process a movie script first."
        
        # Build the context prompt
        prompt = prompts.CHATBOT_PROMPT_TEMPLATE.format(
            script_context=self.script_context,
            semantic_memory=json.dumps(self.memories.get("semantic_memory", {}), indent=2),
            episodic_memory=json.dumps(self.memories.get("episodic_memory", {}), indent=2),
            procedural_memory=json.dumps(self.memories.get("procedural_memory", {}), indent=2),
            question=question
        )
        
        try:
            answer = self.llm.generate(
                prompt=prompt,
                system_message="You are a knowledgeable movie assistant. Answer accurately using the provided context."
            )
            
            # Store in chat history
            self.chat_history.append((question, answer))
            
            return answer
        
        except Exception as e:
            return f"Error generating answer: {str(e)}"
    
    def get_chat_history(self) -> List[Tuple[str, str]]:
        """Get the chat history"""
        return self.chat_history
    
    def clear_history(self):
        """Clear the chat history"""
        self.chat_history = []
