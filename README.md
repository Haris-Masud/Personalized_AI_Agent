# AI Voice Assistant

This project is an AI-powered voice assistant that can process documents, answer questions based on their content, and interact with the user through voice. It leverages technologies like Gemini, ChromaDB, and speech recognition to provide a seamless and intelligent experience.

## Features

*   **Document Processing:** Reads and processes PDF, DOCX, and TXT files.
*   **Text Chunking:** Splits large documents into manageable chunks for efficient processing.
*   **Semantic Search:** Uses ChromaDB for semantic search and retrieval of relevant information.
*   **AI-Powered Responses:** Employs Google's Gemini model to generate intelligent responses to user queries.
*   **Voice Interaction:** Supports text-to-speech and speech-to-text functionalities.
* **RAG Model:** Implements a Retrieval-Augmented Generation (RAG) model for enhanced question answering.

## Prerequisites

*   **Python 3.9+**
*   **Git** (for cloning the repository)
*   **Google Gemini API Key** (You'll need to obtain an API key from Google AI Studio)

## Setup and Installation

Follow these steps to set up and run the AI Voice Assistant:

### 1. Clone the Repository
git clone <repository_url> # Replace <repository_url> with the actual URL
cd AI_voice_assistant


### 2. Create and Activate a Virtual Environment (Windows)
It's highly recommended to use a virtual environment to isolate the project's dependencies.

Create the virtual environment:

 bash 
python -m venv .venv
Activate the virtual environment:

 bash 
.venv\Scripts\activate
You should see (.venv) at the beginning of your command prompt, indicating that the virtual environment is active.

### 3. Install Dependencies
Install the required Python packages using pip:

pip install -r requirements.txt

### 4. Download NLTK Data
The project uses NLTK for sentence tokenization. Download the punkt data:

python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"



### 5. Set the Gemini API Key
Create a .env file: In the root directory of the project (the AI_voice_assistant folder), create a file named .env.
Add your API key: Inside the .env file, add the following line, replacing YOUR_GEMINI_API_KEY with your actual Gemini API key:
 plaintext 
GEMINI_API_KEY=YOUR_GEMINI_API_KEY

### 6. Prepare sample files
Create folder sample in root directory.
Put some .txt, .docx, .pdf files in it.
### 7. Run the Application
Now you can run the main application:
 
python main.py



### Detailed overview of working process 
This will:

Process the sample documents (sample/sample1.txt, sample/sample2.docx, sample/sample3.pdf).
Chunk the text from the documents.
(Commented out in the code) Process the chunks with Gemini and add them to ChromaDB.
Generate a response to the test query: "What services do you offer?".
(Commented out in the code) Convert the response to speech and play it.



### Project Structure
AI_voice_assistant/
├── .venv/                     # Virtual environment (created by you)
├── sample/                   # Sample files for processing
│   ├── sample1.txt
│   ├── sample2.docx
│   └── sample3.pdf
├── src/                      # Source code
│   ├── chromadb_handler.py   # ChromaDB interaction
│   ├── embedder.py           # Text embedding
│   ├── gemini_handler.py     # Gemini API interaction
│   ├── pdf_processor.py      # Document processing
│   ├── rag_model.py          # RAG model implementation
│   └── voice_interface.py    # Voice interaction
├── main.py                   # Main application entry point
├── requirements.txt          # Project dependencies
├── .env                      # Environment variables (API key)
└── README.md                 # This file


### Key Components
main.py: The main script that orchestrates the entire application.
src/pdf_processor.py: Handles reading and chunking of documents.
src/gemini_handler.py: Interacts with the Google Gemini API for text processing and response generation.
src/chromadb_handler.py: Manages the ChromaDB vector database for semantic search.
src/embedder.py: Handles text embedding using Sentence Transformers.
src/rag_model.py: Implements the Retrieval-Augmented Generation model.
src/voice_interface.py: Provides voice interaction capabilities (text-to-speech and speech-to-text).
requirements.txt: Lists all the required python packages.
Future Improvements
Enhanced Voice Interaction: Implement more robust speech recognition and natural language understanding.
Dynamic Document Loading: Allow users to add and remove documents dynamically.
Improved Error Handling: Add more comprehensive error handling and logging.
User Interface: Develop a graphical user interface (GUI) for a more user-friendly experience.
More advanced RAG: Implement more advanced RAG techniques.





python -c "import nltk; nltk.download('punkt')"
