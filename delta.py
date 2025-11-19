"""
Clear and structured prompts for memory extraction
"""

SEMANTIC_MEMORY_PROMPT = """Analyze the following movie script and extract SEMANTIC MEMORY.

Semantic memory includes general knowledge and facts about the movie world.

Extract the following information in JSON format:

{
  "facts": [
    "List of general facts about the movie world, setting, time period",
    "Example: 'The movie is set in 1970s Formula 1 racing'"
  ],
  "concepts": [
    "Key themes and concepts explored in the movie",
    "Example: 'Rivalry', 'Redemption', 'Determination'"
  ],
  "character_traits": {
    "Character Name": ["trait1", "trait2", "trait3"],
    "Example format for each main character"
  },
  "world_building": [
    "Details about the setting, culture, time period, locations",
    "Example: 'European racing circuits in the 1970s'"
  ]
}

Movie Script:
{script}

Return ONLY the JSON object, no additional text or explanation."""

EPISODIC_MEMORY_PROMPT = """Analyze the following movie script and extract EPISODIC MEMORY.

Episodic memory includes specific events, scenes, and the timeline of the story.

Extract the following information in JSON format:

{
  "scenes": [
    {
      "scene_number": "1",
      "location": "Location name",
      "description": "What happens in this scene"
    }
  ],
  "timeline": [
    "Event 1 - Brief description",
    "Event 2 - Brief description",
    "List all major events in chronological order"
  ],
  "key_moments": [
    "Pivotal moment 1 that changes the story",
    "Pivotal moment 2 that affects characters"
  ],
  "plot_points": [
    "Main plot point 1",
    "Main plot point 2",
    "Story beats that drive the narrative forward"
  ]
}

Movie Script:
{script}

Return ONLY the JSON object, no additional text or explanation."""

PROCEDURAL_MEMORY_PROMPT = """Analyze the following movie script and extract PROCEDURAL MEMORY.

Procedural memory includes how things are done, skills demonstrated, and processes shown.

Extract the following information in JSON format:

{
  "skills_demonstrated": [
    "Specific skills shown by characters",
    "Example: 'Formula 1 race car driving', 'Pit crew coordination'"
  ],
  "processes": [
    "Step-by-step processes or methods shown",
    "Example: 'Pre-race car setup: 1) Check tire pressure 2) Adjust wing angles'"
  ],
  "rules_and_protocols": [
    "Rules, protocols, or procedures in the movie world",
    "Example: 'F1 safety regulations', 'Radio communication protocols'"
  ]
}

Movie Script:
{script}

Return ONLY the JSON object, no additional text or explanation."""

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
