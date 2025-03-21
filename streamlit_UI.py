# # streamlit_UI.py

import re
import streamlit as st
import threading
import os
import base64
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs import play
from src.pdf_processor import DocumentProcessor
from src.voice_interface import ImprovedVoiceInterface
from src.gemini_handler import GeminiProcessor
from src.chromadb_handler import ChromaDBHandler
from src.rag_model import RAGModel
import pyttsx3
import time


import pysqlite3
import sys
sys.modules["sqlite3"] = pysqlite3



# Custom CSS for styling
def local_css():
    css = """
    <style>
    /* Set the main background to black */
    .main {
        background-color: black;
        color: white;
    }
    
    /* Also target content area */
    .stApp {
        background-color: black;
    }
    
    
    /* Make sidebar text visible on grey background */
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] span, 
    [data-testid="stSidebar"] div,
    [data-testid="stSidebar"] label {
        color: white;
    }
    
    /* Make sure text is visible on black background */
    h1, h2, h3, p, span, div {
        color: white;
    }
    
    /* Override the default background color for containers */
    .css-18e3th9, .css-1d391kg {
        background-color: black;
    }
    
    /* Adjust header background */
    .css-14xtw13 e8zbici0 {
        background-color: black;
    }

    
    /* Style for Call AI Assistant button (blue and glowing) */
    [data-testid="stButton"] [kind="primary"] {
        background-color: #0066ff;
        color: white;
        border-radius: 10px;
        padding: 15px 32px;
        text-align: center;
        text-decoration: none;
        font-size: 20px;
        margin: 10px 0px;
        cursor: pointer;
        border: none;
        box-shadow: 0 0 15px #0066ff;
    }
    
    [data-testid="stButton"] [kind="primary"]:hover {
        background-color: #0055dd;
        box-shadow: 0 0 25px #0066ff;
        transform: scale(1.05);
    }


    
    .call-button {
        background-color: #0066ff;
        color: white;
        border-radius: 10px;
        padding: 15px 32px;
        text-align: center;
        text-decoration: none;
        font-size: 20px;
        margin: 10px 0px;
        cursor: pointer;
        border: none;
        transition: all 0.3s;
        box-shadow: 0 0 15px #0066ff;
    }
    
    .call-button:hover {
        background-color: #0055dd;
        box-shadow: 0 0 25px #0066ff;
        transform: scale(1.05);
    }
    
    .main-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        margin-top: 20px;
    }
    
    .chat-container {
        border: 1px solid #e6e6e6;
        border-radius: 10px;
        padding: 15px;
        margin-top: 20px;
        max-height: 400px;
        overflow-y: auto;
        width: 100%;
    }
    
    .chat-message-user {
        background-color: #485571;
        border-radius: 10px;
        padding: 10px;
        margin: 5px;
        text-align: right;
    }
    
    .chat-message-ai {
        background-color: #332ac2;
        border-radius: 10px;
        padding: 10px;
        margin: 5px;
        text-align: left;
    }
    
    /* Style for expanders and other widgets on dark background */
    .streamlit-expanderHeader {
        color: white;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# Function to convert the gif to base64 for embedding
def get_base64_gif(gif_path):
    with open(gif_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

# Create a custom button with HTML
def create_button(label, key, is_end_call=False):
    btn_class = "end-call-button" if is_end_call else "call-button"
    button_html = f"""
    <button class="{btn_class}" id="{key}">{label}</button>
    <script>
        document.getElementById("{key}").addEventListener("click", function() {{
            window.parent.postMessage({{type: "streamlit:setComponentValue", value: true, key: "{key}"}}, "*");
        }});
    </script>
    """
    return button_html

class VoiceAIAgent:
    def __init__(self):
        load_dotenv()
        self.doc_processor = DocumentProcessor()
        # self.gemini = GeminiProcessor(os.getenv("GEMINI_API_KEY"))
        self.gemini = GeminiProcessor(st.session_state.get("gemini_api_key"))

        self.db_handler = ChromaDBHandler()
        self.rag = RAGModel(self.gemini, self.db_handler)
        self.voice_interface = ImprovedVoiceInterface()

        self.engine = pyttsx3.init()

        print("Initializing voice AI agent...")
        self.voice_interface.clear_audio_files()
        print("Done")

        self.conversation_history = []
        self.end_call = False

    def process_documents(self, files):
        import tempfile
        temp_paths = []
        for file in files:
            # Create a temporary file with the same extension as the uploaded file
            suffix = os.path.splitext(file.name)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(file.read())
                temp_paths.append(tmp.name)
        for path in temp_paths:
            print(f"\nProcessing: {path}")
            text = self.doc_processor.read_file(path)
            chunks = self.doc_processor.chunk_text(text)
            for i, chunk in enumerate(chunks):
                processed = self.gemini.process_chunk(chunk)
                if processed:
                    self.db_handler.add_documents(
                        documents=[processed['summary']],
                        metadata=[{"source": path, "chunk": i}],
                        ids=[f"{path}_chunk_{i}"]
                    )

    # def play_eleven_labs_audio(self, in_text):
    #     client = ElevenLabs(
    #         api_key=os.getenv("ELEVENLABS_API_KEY"),
    #     )

    #     audio = client.text_to_speech.convert(
    #         text=in_text,
    #         voice_id="cgSgspJ2msm6clMCkdW9",
    #         model_id="eleven_multilingual_v2",
    #         output_format="mp3_44100_128",
    #     )
    #     # return(audio)
    #     play(audio)
                    
    def play_eleven_labs_audio(self, in_text):
        client = ElevenLabs(
            api_key=os.getenv("ELEVENLABS_API_KEY"),
        )

        try:
            audio = client.text_to_speech.convert(
                text=in_text,
                voice_id="cgSgspJ2msm6clMCkdW9",
                model_id="eleven_multilingual_v2",
                output_format="mp3_44100_128",
            )
            play(audio)
        except Exception as e:
            print(f"An error occurred: {e}")

    def simulate_call(self, history=None):
        if history is None:
            history = []

        # Generate and deliver opening
        opening = self.rag.generate_opening("Haris")
        if not opening:
            print("Failed to generate opening pitch")
            return
        
        # st.toast("Call Starting. Please wait until the AI is listening")
        with st.spinner("Starting call. Please wait until the AI is listening..."):
            time.sleep(5)

        opening = self._deliver_opening(opening)

        history.append([None, opening])
        yield history

        while not self.end_call:
            st.toast("Listening...")

            user_input = self.voice_interface.listen_from_mic_with_vad()

            if not user_input:
                print("No input detected, continuing to listen...")
                continue

            print(f"User said: {user_input}")
            history.append([user_input, None])

            # st.toast("The AI is thinking...")
            with st.spinner("The AI is thinking..."):
                response = self.rag.generate_response(user_input, [item[0] for item in history], True)

            if response == "end call":
                with st.spinner("Ending Call..."):
                    ai_response = "Thank you for your time. Have a great day!"
                    self._deliver_response(ai_response)
                    self.end_call = True
                    history.append([None, ai_response])
                    yield history
                    
                break

            response_text = response if isinstance(response, str) else response.get("response", "")
            self._deliver_response(response_text)
            history[-1][1] = response_text  # Update the last history entry with AI response
            yield history
        self.end_call = False #reset end_call

    def manual_input(self, text_input, history):
        if not text_input:
            return history
            
        history.append([text_input, None])
        
        response = self.rag.generate_response(text_input, [item[0] for item in history if item[0]], False)
        
        # if response == "end call":
        #     # st.toast("Ending Call...")
        #     ai_response = "Thank you for your time. Have a great day!"
        #     history.append([None, ai_response])
        #     self.end_call = True
        #     with st.spinner("Ending Call..."):
        #         time.sleep(3)
        #     return history
            
        response_text = response if isinstance(response, str) else response.get("response", "")
        history[-1][1] = response_text
        
        return history

    def _deliver_opening(self, opening):
        """Deliver structured opening pitch"""
        # Handle list responses
        if isinstance(opening, list) and len(opening) > 0:
            opening = opening[0]
            
        if not isinstance(opening, dict):
            print(f"Error: Unexpected opening format - {type(opening)}")
            return

        print("\n=== AI Agent ===")
        full_text = ""
        for key in ['greeting', 'introduction', 'value_proposition', 'next_step_question']:
            text = opening.get(key, "")
            if text:
                print(f"AI: {text}")
                full_text += text + " "

        self.play_eleven_labs_audio(full_text)
        self.conversation_history.append(f"AI: {full_text}")
        return full_text

    def _deliver_response(self, response):
        print("\n=== AI Agent ===\nAI: ", response)
        self.play_eleven_labs_audio(response)

    def clear_database(self):
        try:
            self.db_handler.client.delete_collection("company_data")
            self.db_handler.collection = self.db_handler.client.get_or_create_collection(
                name="company_data",
                embedding_function=self.db_handler.embedding_fn
            )
            return True
        except Exception as e:
            print(f"Error clearing database: {e}")
            return False



agent = VoiceAIAgent()

def process_and_start(files, history):
    file_paths = [file.name for file in files]
    agent.process_documents(file_paths)
    st.session_state['generator'] = agent.simulate_call(history)
    st.session_state['call_active'] = True
    return next(st.session_state['generator'])

def start_only(history):
    st.session_state['generator'] = agent.simulate_call(history)
    st.session_state['call_active'] = True
    return next(st.session_state['generator'])

def end_call():
    if 'generator' in st.session_state and st.session_state['generator']:
        agent.end_call = True
        # Don't try to advance the generator here
        st.session_state['call_active'] = False
        st.session_state['generator'] = None

def is_valid_api_key(api_key):
    """Basic validation for Gemini API key format."""
    # Check if it's a non-empty string with the expected format
    if not api_key or not isinstance(api_key, str):
        return False
    
    # Gemini API keys typically follow this pattern
    pattern = r'^[A-Za-z0-9_-]{39}$'
    return bool(re.match(pattern, api_key))



def main():
    local_css()
    
    # Initialize session states
    if 'history' not in st.session_state:
        st.session_state['history'] = []
    if 'generator' not in st.session_state:
        st.session_state['generator'] = None
    if 'call_active' not in st.session_state:
        st.session_state['call_active'] = False
    if 'show_transcript' not in st.session_state:
        st.session_state['show_transcript'] = False
    if "gemini_valid" not in st.session_state:
        st.session_state["gemini_valid"] = False
    if "gemini_api_key" not in st.session_state:
        st.session_state["gemini_api_key"] = ""   
    if "input_key" not in st.session_state:
        st.session_state["input_key"] = 0  


    # Main container layout with an enhanced title and description
    st.title("🤖 Personalized Voice AI Assistant")
    st.markdown("Easily create and interact with your own personalized AI agent. "
                "Upload documents to build your knowledge base, then initiate a voice or text-based conversation "
                "with your custom AI. This solution leverages advanced retrieval augmented generation (RAG) to give a more personalized experience."
                "Note: No information is permanently stored outside of this session for security reasons, including the data uploaded in the database")
    
    # Sidebar for document upload with improved instructions
    with st.sidebar:

        # API key input and validation
        # Gemini API Key Validation
        if "gemini_valid" not in st.session_state or not st.session_state["gemini_valid"]:
            st.sidebar.header("Gemini API Key Validation")
            gemini_key = st.sidebar.text_input("Please enter a valid Gemini API Key to continue", key="gemini_api_key_input", type="password")
            if st.sidebar.button("Validate Gemini API Key"):
                if gemini_key and is_valid_api_key(gemini_key):
                    st.session_state["gemini_valid"] = True
                    st.session_state["gemini_api_key"] = gemini_key
                    st.sidebar.success("Gemini API Key validated!")

                    agent.clear_database() # clear any previous data in the database


                    st.rerun()
                else:
                    st.sidebar.error("Invalid Gemini API Key!")
            st.stop()  # Prevent further execution until API key is validated






        st.header("Document Upload & Management")
        st.markdown("Upload your documents below to help your AI agent learn and provide personalized responses. "
                    "Supported formats: TXT, DOCX, PDF.")
        uploaded_files = st.file_uploader("Select Documents", accept_multiple_files=True, type=["txt", "docx", "pdf"])
        
        if st.button("Add Documents to Personal AI") and uploaded_files:
            # st.toast("Adding documents. Please wait")
            with st.spinner("Adding documents. Please wait..."):
                agent.process_documents(uploaded_files)  # Pass the actual file objects
            st.success(f"Added {len(uploaded_files)} documents to the database!")
            # st.session_state["uploaded_files"] = []  # Clear the file uploader list
        
        if st.button("Clear Knowledge Base"):
            if agent.clear_database():
                st.success("Knowledge base cleared successfully!")
            else:
                st.error("Failed to clear knowledge base!")
    
    # Main content area
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col2:
        # Display either static image or animation based on call status
        if st.session_state['call_active']:
            # Display the audio animation gif when call is active
            try:
                st.image("test3.gif", use_container_width=True)
            except:
                st.warning("test3.gif not found. Please add it to your project directory.")
        else:
            # Display static image when no call is active
            try:
                st.image("test3.png", use_container_width=True)
            except:
                st.warning("test3.png not found. Please add it to your project directory.")
        
        # Call/End Call button with clearer labels
        if not st.session_state['call_active']:
            if st.button("Call AI Assistant", key="call_btn", use_container_width=True, type="primary"):
                st.session_state['history'] = start_only(st.session_state['history'])
                st.rerun()
        else:
            if st.button("End AI Call", key="end_btn", use_container_width=True, type="primary"):
                with st.spinner("Ending Call..."):
                    end_call()
                st.rerun()
        
        # Transcript dropdown with updated header
        with st.expander("View the conversation history or chat", expanded=st.session_state['show_transcript']):
            # Display chat history
            for i, message in enumerate(st.session_state['history']):
                if message[0]:  # User message
                    st.markdown(f"<div class='chat-message-user'><strong>You:</strong> {message[0]}</div>", unsafe_allow_html=True)
                if message[1]:  # AI message
                    st.markdown(f"<div class='chat-message-ai'><strong>AI:</strong> {message[1]}</div>", unsafe_allow_html=True)
            
            # Text input for manual messages
            # text_input = st.text_input("Type your message:", key="text_input")
            # if st.button("Send", key="send_text"):
            #     if text_input: 
            #         st.toast("Fetching response. Please wait")
            #         st.session_state['history'] = agent.manual_input(text_input, st.session_state['history'])
            #         st.session_state["text_input"] = ""  # Clear the input field
            #         st.rerun()
                    
            text_input = st.text_input("Type your message:", key=f"text_input_{st.session_state['input_key']}")

            if st.button("Send", key="send_text"):
                if text_input:
                    # st.toast("Fetching response. Please wait")
                    with st.spinner("Fetching response. Please wait..."):
                        st.session_state['history'] = agent.manual_input(text_input, st.session_state['history'])
                    st.session_state["input_key"] += 1  # Change key to reset input
                    st.rerun()
    
    # Check if we need to update the UI from the generator
    if st.session_state['generator'] and st.session_state['call_active']:
        try:
            st.session_state['history'] = next(st.session_state['generator'])
            st.rerun()
        except StopIteration:
            st.session_state['call_active'] = False
            st.session_state['generator'] = None
            st.rerun()

if __name__ == "__main__":
    main()
