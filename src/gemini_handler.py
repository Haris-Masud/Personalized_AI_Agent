# gemini_handler.py
import google.generativeai as genai
import json
import re

class GeminiProcessor:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash',
            generation_config={"response_mime_type": "application/json"})
    
    def process_chunk(self, text_chunk):
        prompt = f"""
    Please analyze the following text and extract key information. Return the results as a JSON object with the following structure:

    {{
      "key_points": ["List of main ideas, figures, or significant details with their context."],
      "summary": "A concise summary of the text, limited to 50 words and focusing on the most important information.",
      "keywords": ["List of relevant keywords extracted from the text."]
    }}

    Text:
    {text_chunk}

    Respond with the JSON object ONLY. Do not include any additional text or explanations.
    """

        try:
            response = self.model.generate_content(prompt)
            # Clean response and extract JSON
            clean_response = self._extract_json(response.text)
            return json.loads(clean_response)
        except Exception as e:
            print(f"Gemini API Error: {e}")
            print(f"Raw response: {response.text if 'response' in locals() else ''}")
            return None

    def _extract_json(self, text):
        """Handle common Gemini response formatting issues"""
        # Remove markdown code blocks
        text = re.sub(r'```json|```', '', text)
        # Remove extra whitespace
        text = text.strip()
        # Fix common escaping issues
        text = text.replace('\\"', '"').replace("\\'", "'")
        return text
