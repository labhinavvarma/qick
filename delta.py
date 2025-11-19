"""
Clear and structured prompts for memory extraction
"""

SEMANTIC_MEMORY_PROMPT = """You are a JSON extraction expert. Extract semantic memory from this movie script.

IMPORTANT: Return ONLY valid JSON. No markdown, no code blocks, no explanations. Just the raw JSON object.

Extract this exact structure:
{{
  "facts": ["fact1", "fact2", "fact3"],
  "concepts": ["concept1", "concept2"],
  "character_traits": {{"Character Name": ["trait1", "trait2"]}},
  "world_building": ["detail1", "detail2"]
}}

Semantic memory = general knowledge about the movie world
- facts: General facts about setting, time period, genre
- concepts: Themes like rivalry, redemption, love
- character_traits: Main characters and their personality traits
- world_building: Setting details, locations, culture, time period

Movie Script:
{script}

Return valid JSON only. Start with {{ and end with }}. No other text.

EPISODIC_MEMORY_PROMPT = """You are a JSON extraction expert. Extract episodic memory from this movie script.

IMPORTANT: Return ONLY valid JSON. No markdown, no code blocks, no explanations. Just the raw JSON object.

Extract this exact structure:
{{
  "scenes": [{{"scene_number": "1", "location": "Place", "description": "What happens"}}],
  "timeline": ["Event 1", "Event 2", "Event 3"],
  "key_moments": ["Pivotal moment 1", "Pivotal moment 2"],
  "plot_points": ["Plot point 1", "Plot point 2"]
}}

Episodic memory = specific events and timeline
- scenes: Individual scenes with number, location, description
- timeline: Chronological list of major events
- key_moments: Pivotal moments that change the story
- plot_points: Main story beats that drive narrative

Movie Script:
{script}

Return valid JSON only. Start with {{ and end with }}. No other text.

PROCEDURAL_MEMORY_PROMPT = """You are a JSON extraction expert. Extract procedural memory from this movie script.

IMPORTANT: Return ONLY valid JSON. No markdown, no code blocks, no explanations. Just the raw JSON object.

Extract this exact structure:
{{
  "skills_demonstrated": ["skill1", "skill2", "skill3"],
  "processes": ["process1", "process2"],
  "rules_and_protocols": ["rule1", "rule2"]
}}

Procedural memory = how things are done
- skills_demonstrated: Specific skills shown by characters
- processes: Step-by-step methods or procedures shown
- rules_and_protocols: Rules, regulations, or protocols in the movie

Movie Script:
{script}

Return valid JSON only. Start with {{ and end with }}. No other text.

CHATBOT_PROMPT_TEMPLATE = """You are a movie expert assistant. Answer the user's question using the context provided below.

MOVIE SCRIPT CONTEXT:
{script_context}

SEMANTIC MEMORY (Facts, Concepts, Characters):
{semantic_memory}

EPISODIC MEMORY (Scenes, Timeline, Events):
{episodic_memory}

PROCEDURAL MEMORY (Skills, Processes, Rules):
{procedural_memory}

USER QUESTION: {question}

Provide a detailed and accurate answer based on the context above. Reference specific information from the memories when relevant."""
