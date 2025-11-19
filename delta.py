"""
LLM Client for sfassist API
"""

import requests
import json
import uuid
import urllib3
from typing import Dict, Any

# Disable SSL warnings for internal environments
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class SFAssistClient:
    """Client for interacting with sfassist API"""
    
    def __init__(self, api_url: str, api_key: str, app_id: str, aplctn_cd: str, model: str):
        self.api_url = api_url
        self.api_key = api_key
        self.app_id = app_id
        self.aplctn_cd = aplctn_cd
        self.model = model
    
    def generate(self, prompt: str, system_message: str = "", session_id: str = None) -> str:
        """
        Generate a response from the LLM
        
        Args:
            prompt: The user prompt/question
            system_message: System message for the LLM
            session_id: Optional session ID
        
        Returns:
            The LLM's response as a string
        """
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        # Build payload
        payload = {
            "query": {
                "aplctn_cd": self.aplctn_cd,
                "app_id": self.app_id,
                "api_key": self.api_key,
                "method": "cortex",
                "model": self.model,
                "sys_msg": system_message,
                "limit_convs": "0",
                "prompt": {
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                },
                "app_lvl_prefix": "",
                "user_id": "",
                "session_id": session_id
            }
        }
        
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json",
            "Authorization": f'Snowflake Token="{self.api_key}"'
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                verify=False,
                timeout=120
            )
            
            if response.status_code == 200:
                raw = response.text
                
                # Clean the response
                if "end_of_stream" in raw:
                    answer, _, _ = raw.partition("end_of_stream")
                    return answer.strip()
                else:
                    return raw.strip()
            else:
                raise Exception(f"API Error {response.status_code}: {response.text}")
        
        except Exception as e:
            raise Exception(f"LLM API request failed: {str(e)}")
    
    def generate_json(self, prompt: str, system_message: str = "") -> Dict[str, Any]:
        """
        Generate a JSON response from the LLM
        
        Args:
            prompt: The user prompt
            system_message: System message for the LLM
        
        Returns:
            Parsed JSON response as a dictionary
        """
        response = self.generate(prompt, system_message)
        
        # Clean the response
        response = response.strip()
        
        # Remove markdown code blocks if present
        if response.startswith("```json"):
            response = response.replace("```json", "").replace("```", "").strip()
        elif response.startswith("```"):
            response = response.replace("```", "").strip()
        
        # Try to extract JSON from the response
        try:
            # First, try direct parsing
            return json.loads(response)
        except json.JSONDecodeError as e:
            # Try to find JSON in the response
            start_idx = response.find('{')
            end_idx = response.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                json_str = response[start_idx:end_idx+1]
                
                # Clean common JSON errors
                json_str = json_str.replace('\n', '\\n')  # Fix newlines
                json_str = json_str.replace('\r', '\\r')  # Fix carriage returns
                json_str = json_str.replace('\t', '\\t')  # Fix tabs
                
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    # Last attempt - try to fix common issues
                    # Replace single quotes with double quotes
                    json_str = json_str.replace("'", '"')
                    
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        raise Exception(f"Could not parse JSON. Original error: {str(e)}. Response preview: {response[:500]}")
            else:
                raise Exception(f"No valid JSON found in response. Response preview: {response[:500]}")
              
