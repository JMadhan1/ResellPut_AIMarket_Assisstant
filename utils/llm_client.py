import os
import re
import json
import logging
import requests
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

class BaseLLMClient(ABC):
    """Abstract base class for LLM clients"""

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate response from LLM"""
        pass

    def extract_json(self, response: str) -> str:
        """Extract JSON from LLM response"""
        # Try to find JSON block
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json_match.group()

        # If no JSON block found, try to clean up the response
        response = response.strip()
        if response.startswith('```json'):
            response = response[7:]
        if response.startswith('```'):
            response = response[3:]
        if response.endswith('```'):
            response = response[:-3]

        return response.strip()

class GroqLLMClient(BaseLLMClient):
    """Groq API client for fast inference"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.groq.com/openai/v1"
        self.model = "mixtral-8x7b-32768"
        self.logger = logging.getLogger(self.__class__.__name__)

    def generate(self, prompt: str) -> str:
        """Generate response using Groq API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 1024
        }

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )

            response.raise_for_status()
            data = response.json()

            if 'choices' in data and len(data['choices']) > 0:
                return data['choices'][0]['message']['content']
            else:
                raise Exception("No response generated")

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Groq API request failed: {str(e)}")
            raise Exception(f"Groq API error: {str(e)}")

class HuggingFaceLLMClient(BaseLLMClient):
    """Hugging Face Inference API client"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model = "mistralai/Mistral-7B-Instruct-v0.1"
        self.base_url = f"https://api-inference.huggingface.co/models/{self.model}"
        self.logger = logging.getLogger(self.__class__.__name__)

    def generate(self, prompt: str) -> str:
        """Generate response using Hugging Face API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "inputs": prompt,
            "parameters": {
                "temperature": 0.1,
                "max_new_tokens": 1024,
                "do_sample": True
            }
        }

        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=30
            )

            response.raise_for_status()
            data = response.json()

            if isinstance(data, list) and len(data) > 0:
                return data[0].get('generated_text', '').replace(prompt, '').strip()
            elif isinstance(data, dict) and 'generated_text' in data:
                return data['generated_text'].replace(prompt, '').strip()
            else:
                raise Exception("Unexpected response format")

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Hugging Face API request failed: {str(e)}")
            raise Exception(f"Hugging Face API error: {str(e)}")

class GeminiLLMClient(BaseLLMClient):
    """Google Gemini API client"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model = "gemini-2.5-flash"
        self.logger = logging.getLogger(self.__class__.__name__)

        if not GEMINI_AVAILABLE:
            raise ImportError("google-genai package not available")

        try:
            self.client = genai.Client(api_key=api_key)
        except Exception as e:
            self.logger.error(f"Failed to initialize Gemini client: {str(e)}")
            raise

    def generate(self, prompt: str) -> str:
        """Generate response using Gemini API"""
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=2000
                )
            )

            if not response:
                self.logger.error("No response from Gemini")
                raise Exception("No response from Gemini")

            # Extract text from response with multiple fallback methods
            text_content = None
            
            # Method 1: Check candidates
            if hasattr(response, 'candidates') and response.candidates:
                for candidate in response.candidates:
                    if hasattr(candidate, 'content') and candidate.content:
                        if hasattr(candidate.content, 'parts') and candidate.content.parts:
                            for part in candidate.content.parts:
                                if hasattr(part, 'text') and part.text and part.text.strip():
                                    text_content = part.text.strip()
                                    break
                    if text_content:
                        break
            
            # Method 2: Direct text attribute
            if not text_content and hasattr(response, 'text') and response.text:
                text_content = response.text.strip()
            
            # Method 3: Check if response is a string
            if not text_content and isinstance(response, str):
                text_content = response.strip()
            
            # Method 4: Convert response to string and extract
            if not text_content:
                response_str = str(response)
                if response_str and response_str != "None":
                    # Try to extract JSON-like content
                    import re
                    json_match = re.search(r'\{.*\}', response_str, re.DOTALL)
                    if json_match:
                        text_content = json_match.group()

            if text_content:
                return text_content

            # Log the full response for debugging
            self.logger.error(f"Empty response from Gemini. Response object: {type(response)}, Response: {response}")
            raise Exception("Empty response from Gemini")

        except Exception as e:
            self.logger.error(f"Gemini API request failed: {str(e)}")
            raise Exception(f"Gemini API error: {str(e)}")

class MockLLMClient(BaseLLMClient):
    """Mock LLM client for testing"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def generate(self, prompt: str) -> str:
        """Generate mock response based on prompt content"""
        self.logger.info("Using mock LLM client")

        if "price" in prompt.lower() or "pricing" in prompt.lower():
            return self._generate_mock_price_response()
        elif "moderate" in prompt.lower() or "message" in prompt.lower():
            return self._generate_mock_moderation_response()
        else:
            return '{"error": "Unknown prompt type", "confidence": 0.5}'

    def _generate_mock_price_response(self) -> str:
        """Generate mock price suggestion response"""
        return '''{
            "suggested_price_range": {
                "min": 15000,
                "max": 18000
            },
            "reasoning": "Based on market analysis, this product shows typical depreciation for its category and age. Similar items in the market range from ₹15,000 to ₹18,000.",
            "confidence": 0.75,
            "market_position": "fairly_priced",
            "recommendations": [
                "Price is competitive for current market conditions",
                "Consider slight reduction if item doesn't sell within 2 weeks"
            ]
        }'''

    def _generate_mock_moderation_response(self) -> str:
        """Generate mock moderation response"""
        return '''{
            "status": "safe",
            "reason": "Message contains normal product inquiry without policy violations",
            "confidence": 0.9,
            "detected_elements": [],
            "severity": "low",
            "action_recommended": "none"
        }'''

class LLMClientFactory:
    """Factory for creating LLM clients"""

    @staticmethod
    def create_client() -> BaseLLMClient:
        """Create appropriate LLM client based on available API keys"""
        # Check for Google/Gemini API keys
        gemini_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        groq_key = os.getenv("GROQ_API_KEY")
        hf_key = os.getenv("HUGGINGFACE_API_KEY")

        if gemini_key and GEMINI_AVAILABLE:
            logging.info("Using Gemini LLM client")
            return GeminiLLMClient(gemini_key)
        elif groq_key:
            logging.info("Using Groq LLM client")
            return GroqLLMClient(groq_key)
        elif hf_key:
            logging.info("Using Hugging Face LLM client")
            return HuggingFaceLLMClient(hf_key)
        else:
            logging.warning("No API keys found, using mock LLM client")
            return MockLLMClient()