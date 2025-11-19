"""
Movie Memory Extractor - Streamlit Application
Main application file with UI
"""

import streamlit as st
import json
import pandas as pd
from io import StringIO

# Import our modules
import config
from llm_client import SFAssistClient
from memory_extractor import MemoryExtractor
from chatbot import MovieChatbot


# === Page Configuration ===
st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon=config.APP_ICON,
    layout="wide"
)

# === Initialize Session State ===
if "memories" not in st.session_state:
    st.session_state.memories = None

if "script_text" not in st.session_state:
    st.session_state.script_text = None

if "chatbot" not in st.session_state:
    st.session_state.chatbot = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "extraction_complete" not in st.session_state:
    st.session_state.extraction_complete = False


# === Initialize LLM Client ===
@st.cache_resource
def get_llm_client():
    """Initialize and cache the LLM client"""
    return SFAssistClient(
        api_url=config.API_URL,
        api_key=config.API_KEY,
        app_id=config.APP_ID,
        aplctn_cd=config.APLCTN_CD,
        model=config.MODEL
    )


# === Helper Functions ===
def display_semantic_memory(semantic_mem):
    """Display semantic memory in a structured format"""
    st.subheader("🧠 Semantic Memory")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📌 Facts:**")
        if semantic_mem.get("facts"):
            for fact in semantic_mem["facts"]:
                st.markdown(f"- {fact}")
        
        st.markdown("**💡 Concepts:**")
        if semantic_mem.get("concepts"):
            for concept in semantic_mem["concepts"]:
                st.markdown(f"- {concept}")
    
    with col2:
        st.markdown("**👥 Character Traits:**")
        if semantic_mem.get("character_traits"):
            for char, traits in semantic_mem["character_traits"].items():
                st.markdown(f"**{char}:** {', '.join(traits)}")
        
        st.markdown("**🌍 World Building:**")
        if semantic_mem.get("world_building"):
            for wb in semantic_mem["world_building"]:
                st.markdown(f"- {wb}")


def display_episodic_memory(episodic_mem):
    """Display episodic memory in a structured format"""
    st.subheader("📖 Episodic Memory")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Scenes", "Timeline", "Key Moments", "Plot Points"])
    
    with tab1:
        if episodic_mem.get("scenes"):
            scenes_df = pd.DataFrame(episodic_mem["scenes"])
            st.dataframe(scenes_df, use_container_width=True)
        else:
            st.info("No scenes extracted")
    
    with tab2:
        if episodic_mem.get("timeline"):
            for i, event in enumerate(episodic_mem["timeline"], 1):
                st.markdown(f"**{i}.** {event}")
        else:
            st.info("No timeline extracted")
    
    with tab3:
        if episodic_mem.get("key_moments"):
            for moment in episodic_mem["key_moments"]:
                st.markdown(f"⭐ {moment}")
        else:
            st.info("No key moments extracted")
    
    with tab4:
        if episodic_mem.get("plot_points"):
            for point in episodic_mem["plot_points"]:
                st.markdown(f"📍 {point}")
        else:
            st.info("No plot points extracted")


def display_procedural_memory(procedural_mem):
    """Display procedural memory in a structured format"""
    st.subheader("⚙️ Procedural Memory")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**🎯 Skills Demonstrated:**")
        if procedural_mem.get("skills_demonstrated"):
            for skill in procedural_mem["skills_demonstrated"]:
                st.markdown(f"- {skill}")
        else:
            st.info("No skills extracted")
    
    with col2:
        st.markdown("**🔄 Processes:**")
        if procedural_mem.get("processes"):
            for process in procedural_mem["processes"]:
                st.markdown(f"- {process}")
        else:
            st.info("No processes extracted")
    
    with col3:
        st.markdown("**📋 Rules & Protocols:**")
        if procedural_mem.get("rules_and_protocols"):
            for rule in procedural_mem["rules_and_protocols"]:
                st.markdown(f"- {rule}")
        else:
            st.info("No rules extracted")


# === Main Application ===
def main():
    st.title(config.APP_TITLE)
    st.markdown("Upload a movie script to extract semantic, episodic, and procedural memories!")
    
    # Sidebar for file upload
    with st.sidebar:
        st.header("📤 Upload Movie Script")
        
        uploaded_file = st.file_uploader(
            "Choose a text file",
            type=["txt"],
            help="Upload a movie script in .txt format"
        )
        
        if uploaded_file is not None:
            # Read the script
            stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
            script_text = stringio.read()
            
            st.success(f"✅ File loaded: {uploaded_file.name}")
            st.info(f"📄 Length: {len(script_text)} characters")
            
            # Check length
            if len(script_text) > config.MAX_SCRIPT_LENGTH:
                st.warning(f"⚠️ Script is long. Using first {config.MAX_SCRIPT_LENGTH} characters.")
                script_text = script_text[:config.MAX_SCRIPT_LENGTH]
            
            # Store in session state
            st.session_state.script_text = script_text
            
            # Extract button
            if st.button("🚀 Extract Memories", use_container_width=True, type="primary"):
                with st.spinner("Extracting memories... This may take 1-2 minutes..."):
                    try:
                        # Initialize components
                        llm_client = get_llm_client()
                        extractor = MemoryExtractor(llm_client)
                        
                        # Progress tracking
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        def update_progress(message, percent):
                            status_text.text(message)
                            progress_bar.progress(percent / 100)
                        
                        # Extract memories
                        memories = extractor.extract_all_memories(
                            script_text,
                            progress_callback=update_progress
                        )
                        
                        # Store in session state
                        st.session_state.memories = memories
                        st.session_state.extraction_complete = True
                        
                        # Initialize chatbot
                        chatbot = MovieChatbot(llm_client)
                        chatbot.set_context(script_text, memories)
                        st.session_state.chatbot = chatbot
                        
                        # Save to JSON
                        json_filename = "movie_memories.json"
                        extractor.save_memories_to_json(memories, json_filename)
                        
                        progress_bar.progress(100)
                        status_text.text("✅ Extraction complete!")
                        st.success("🎉 Memories extracted successfully!")
                        
                    except Exception as e:
                        st.error(f"❌ Error during extraction: {str(e)}")
        
        # Download JSON button
        if st.session_state.memories:
            st.divider()
            json_str = json.dumps(st.session_state.memories, indent=2)
            st.download_button(
                label="💾 Download Memories JSON",
                data=json_str,
                file_name="movie_memories.json",
                mime="application/json",
                use_container_width=True
            )
    
    # Main content area
    if st.session_state.extraction_complete and st.session_state.memories:
        
        # Create tabs for different views
        tab1, tab2, tab3 = st.tabs(["📊 Memory Tables", "💬 Chatbot", "📄 Raw JSON"])
        
        with tab1:
            st.header("Extracted Memories")
            
            # Display all memories
            display_semantic_memory(st.session_state.memories.get("semantic_memory", {}))
            st.divider()
            display_episodic_memory(st.session_state.memories.get("episodic_memory", {}))
            st.divider()
            display_procedural_memory(st.session_state.memories.get("procedural_memory", {}))
        
        with tab2:
            st.header("🤖 Movie Chatbot")
            st.markdown("Ask questions about the movie using the extracted memories!")
            
            # Chat interface
            chat_container = st.container()
            
            # Display chat history
            with chat_container:
                if st.session_state.chatbot and st.session_state.chatbot.chat_history:
                    for question, answer in st.session_state.chatbot.chat_history:
                        with st.chat_message("user"):
                            st.write(question)
                        with st.chat_message("assistant"):
                            st.write(answer)
            
            # Chat input
            question = st.chat_input("Ask a question about the movie...")
            
            if question:
                # Display user question
                with st.chat_message("user"):
                    st.write(question)
                
                # Get chatbot response
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        answer = st.session_state.chatbot.ask(question)
                        st.write(answer)
            
            # Clear chat button
            if st.button("🗑️ Clear Chat History"):
                st.session_state.chatbot.clear_history()
                st.rerun()
        
        with tab3:
            st.header("Raw JSON Output")
            st.json(st.session_state.memories)
    
    else:
        # Welcome message
        st.info("👈 Upload a movie script from the sidebar to get started!")
        
        st.markdown("""
        ### How it works:
        
        1. **Upload** a movie script (.txt file) using the sidebar
        2. **Extract** three types of memories:
           - 🧠 **Semantic Memory**: Facts, concepts, character traits, world-building
           - 📖 **Episodic Memory**: Scenes, timeline, key moments, plot points
           - ⚙️ **Procedural Memory**: Skills, processes, rules demonstrated
        3. **View** the extracted memories in structured tables
        4. **Chat** with an AI assistant about the movie using the memories
        5. **Download** the memories as JSON for later use
        
        ### Features:
        - ✅ Automatic memory extraction using AI
        - ✅ Structured display in tables
        - ✅ Interactive chatbot with movie context
        - ✅ JSON export functionality
        - ✅ Support for any movie script
        """)


if __name__ == "__main__":
    main()
