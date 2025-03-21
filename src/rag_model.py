# rag_model.py
import json


class RAGModel:
    def __init__(self, gemini_processor, db_handler):
        self.gemini = gemini_processor
        self.db = db_handler
        self.conversation_state = {}

    def fetch_context(self, query):
        """Retrieve relevant context from database"""
        return self.db.query(query)

    def generate_opening(self, client_name="Sir/Ma'am"):
        """
        Generate initial marketing pitch using company information
        Returns structured response with suggested next steps
        """
        context = self.db.query("company services overview")
        prompt = f"""Create a friendly opening pitch using this context: {context}
        Structure the response as JSON with these keys:
        {{
            "greeting": "Personalized greeting with {client_name}",
            "introduction": "1-sentence company introduction",
            "value_proposition": "Main value proposition",
            "services": ["list", "of", "3-5", "key services"],
            "next_step_question": "A question to engage the client"
        }}
        Make it sound natural and conversational."""
        
        try:
            response = self.gemini.model.generate_content(prompt)
            clean_response = self._clean_json(response.text)
            return json.loads(clean_response)
        except Exception as e:
            print(f"Error generating opening: {e}")
            return self._default_opening()

    def generate_response(self, user_input, conversation_history=[], audio_check=False):
        """
        Generate response to client questions with context awareness
        Maintains conversation history for continuity
        """
        context = self.fetch_context(user_input)
        # history_str = "\n".join(conversation_history[-10:])  # Keep last 10 exchanges
        history_str = "\n".join(filter(None, conversation_history[-10:])) # Filter out None values

        if audio_check:
            audio_condition = "- If a question seems incomplete or does not make sense ( like a random phrase or cut off in the middle of a sentence), it might be an issue with the audio, ask the user to kindly repeat themselves. "
        else:
            audio_condition = ""
        
        prompt = f"""Respond to client query considering:
        Context: {context}
        History: {history_str}
        Query: {user_input}
        
        Requirements:
        - Be concise (1-2 sentences)
        - Maintain professional yet friendly tone
        - If unsure, offer to connect to human representative
        - Include natural transition to next question
        - Return only the response sentence as simple text, no additional commentary or formatting
        - ALWAYS return the response as "response": "response text" 
        - Do not mention getting the user in contact with a representative, try handling everything yourself, as far as you can.
        {audio_condition}
        
        IMPORTANT: If the client mentions anything that indicates they are done with the call and want to end it, simply return "response": "end call", nothing else"""
        
        response = self.gemini.model.generate_content(prompt)

        raw_text = response.text.strip()
        
        print("\n\nresponse: ", response.text, "\n\n")
        # Parse the JSON and extract the "response" key
        try:
            data = json.loads(raw_text)
            return data.get("response", "")
        except json.JSONDecodeError:
            # If the JSON fails to parse, return the raw text
            return {"response": raw_text}


    def _clean_json(self, text):
        """Clean JSON responses from Gemini"""
        try:
            # Remove markdown code blocks and strip whitespace
            text = text.replace('```json', '').replace('```', '').strip()
            
            # Handle cases where response is a list
            if text.startswith('['):
                return text[1:-1]  # Remove brackets if it's a single-item list
            return text
        except Exception as e:
            print(f"Error cleaning JSON: {e}")
            return '{}'

    def _default_opening(self):
        """Fallback opening structure"""
        return {
            "greeting": "Good day!",
            "introduction": "We're Quantum Marketing Solutions, leaders in digital innovation.",
            "value_proposition": "We help businesses grow through data-driven marketing strategies.",
            "services": ["Social Media Management", "SEO Optimization", "Data Analytics"],
            "next_step_question": "Would you like me to explain how we can boost your online presence?"
        }