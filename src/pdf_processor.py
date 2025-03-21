# pdf_processor.py
import os
import PyPDF2
import docx2txt
import nltk
from nltk.tokenize import sent_tokenize

class DocumentProcessor:
    def __init__(self):
        self.supported_formats = ['.pdf', '.docx', '.txt']
        self._initialize_nltk()

    def _initialize_nltk(self):
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            print("Downloading NLTK punkt data...")
            nltk.download('punkt')
        try:
            nltk.data.find('tokenizers/punkt_tab')
        except LookupError:
            print("Downloading NLTK punkt_tab data...")
            nltk.download('punkt_tab')

    def read_file(self, file_path):
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.pdf':
            return self._read_pdf(file_path)
        elif ext == '.docx':
            return self._read_docx(file_path)
        elif ext == '.txt':
            return self._read_txt(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    def _read_pdf(self, file_path):
        text = ""
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text()
        return text

    def _read_docx(self, file_path):
        return docx2txt.process(file_path)

    def _read_txt(self, file_path):
        encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252']
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as file:
                    return file.read()
            except UnicodeDecodeError:
                continue
        raise UnicodeDecodeError(f"Failed to decode {file_path} with tried encodings")

    def chunk_text(self, text, chunk_size=1000, overlap=200):
        """
        Split text into chunks that preserve sentence boundaries
        with configurable overlap between chunks
        """
        try:
            sentences = sent_tokenize(text)
        except Exception as e:
            print(f"Error in sentence tokenization: {e}")
            # Fallback to simple chunking if tokenization fails
            return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
        
        chunks = []
        current_chunk = []
        current_length = 0
        overlap_buffer = []

        for sentence in sentences:
            sentence_length = len(sentence)
            
            # If adding this sentence would exceed chunk size
            if current_length + sentence_length > chunk_size:
                if current_chunk:
                    # Save current chunk
                    chunks.append(" ".join(current_chunk))
                    
                    # Preserve overlap for next chunk
                    overlap_buffer = current_chunk[-self._num_overlap_sentences(current_chunk, overlap):]
                    current_chunk = overlap_buffer.copy()
                    current_length = sum(len(s) for s in current_chunk)
                
            # Add sentence to current chunk
            current_chunk.append(sentence)
            current_length += sentence_length

        # Add the final chunk
        if current_chunk:
            chunks.append(" ".join(current_chunk))
            
        return chunks

    def _num_overlap_sentences(self, sentences, overlap_size):
        """Calculate how many sentences to overlap based on target overlap size"""
        total = 0
        count = 0
        for sentence in reversed(sentences):
            total += len(sentence)
            count += 1
            if total >= overlap_size:
                break
        return count