import json
import re
from typing import Dict, Any
from agents.base_agent import BaseAgent

class ChatModeratorAgent(BaseAgent):
    """Agent for moderating chat messages and detecting policy violations"""
    
    def __init__(self):
        super().__init__()
        
        # Phone number patterns for Indian mobile numbers
        self.phone_patterns = [
            r'\b\d{10}\b',                          # 10 digits
            r'\b\+91[\s-]?\d{10}\b',               # +91 with 10 digits
            r'\b91[\s-]?\d{10}\b',                 # 91 with 10 digits
            r'\b\d{3}[\s-]\d{3}[\s-]\d{4}\b',     # XXX-XXX-XXXX format
            r'\b\d{5}[\s-]\d{5}\b',               # XXXXX-XXXXX format
        ]
        
        # Abusive/spam keywords
        self.abusive_keywords = [
            'fraud', 'scam', 'cheat', 'fake', 'stupid', 'idiot', 'fool',
            'urgent', 'hurry', 'cash only', 'advance payment', 'western union',
            'money gram', 'lottery', 'winner', 'congratulations', 'selected'
        ]
        
        # External platform keywords
        self.external_platforms = [
            'whatsapp', 'telegram', 'facebook', 'instagram', 'email', 'gmail',
            'yahoo', 'hotmail', 'call me', 'text me', 'dm me', 'message me'
        ]
    
    def _validate_input(self, data: Dict[str, Any]) -> None:
        """Validate chat moderator input"""
        if 'message' not in data:
            raise ValueError("Missing required field: message")
        
        if not isinstance(data['message'], str):
            raise ValueError("Message must be a string")
        
        if len(data['message'].strip()) == 0:
            raise ValueError("Message cannot be empty")
        
        if len(data['message']) > 1000:
            raise ValueError("Message too long (max 1000 characters)")
    
    def _generate_prompt(self, data: Dict[str, Any]) -> str:
        """Generate moderation prompt"""
        message = data['message']
        context = data.get('context', 'No additional context')
        
        # Pre-analyze for obvious violations
        phone_detected = self._detect_phone_number(message)
        abusive_detected = self._detect_abusive_content(message)
        external_platform_detected = self._detect_external_platforms(message)
        
        return f"""You are an expert content moderator for a trusted marketplace platform.

MESSAGE TO ANALYZE: "{message}"

CONTEXT: {context}

PRE-ANALYSIS RESULTS:
- Phone number detected: {phone_detected}
- Abusive content detected: {abusive_detected}
- External platform mentioned: {external_platform_detected}

MODERATION GUIDELINES:

SAFE CONTENT:
- Normal product inquiries
- Price negotiations
- Meetup arrangements (without personal details)
- Product condition questions
- Delivery and payment discussions

PHONE NUMBER DETECTION:
- Any 10-digit Indian mobile numbers
- Numbers with country codes (+91, 91)
- Numbers in any format (spaces, dashes, dots)
- Even if numbers are disguised (o for 0, etc.)

ABUSIVE/SPAM INDICATORS:
- Offensive language or threats
- Promotional content unrelated to the product
- Repetitive messages
- Requests for external communication
- Suspicious urgent language
- Fraud/scam attempts

POLICY VIOLATIONS:
- Asking for personal information
- Attempting to bypass platform
- Fraudulent behavior patterns
- Requesting advance payments
- Promoting external services

Respond with ONLY this JSON structure:
{{
    "status": "<safe|abusive|phone_detected|policy_violation>",
    "reason": "<specific_explanation>",
    "confidence": <0.0_to_1.0>,
    "detected_elements": ["<specific_problematic_parts>"],
    "severity": "<low|medium|high>",
    "action_recommended": "<none|warn|block|review>"
}}"""
    
    def _detect_phone_number(self, message: str) -> bool:
        """Detect phone numbers using regex patterns"""
        message_clean = re.sub(r'[^\d\+\s-]', '', message)  # Keep only digits, +, spaces, dashes
        
        for pattern in self.phone_patterns:
            if re.search(pattern, message_clean):
                return True
        return False
    
    def _detect_abusive_content(self, message: str) -> bool:
        """Detect abusive content using keyword matching"""
        message_lower = message.lower()
        
        for keyword in self.abusive_keywords:
            if keyword in message_lower:
                return True
        return False
    
    def _detect_external_platforms(self, message: str) -> bool:
        """Detect mentions of external platforms"""
        message_lower = message.lower()
        
        for platform in self.external_platforms:
            if platform in message_lower:
                return True
        return False
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse and validate LLM response"""
        try:
            # Extract JSON from response
            json_str = self.llm_client.extract_json(response)
            result = json.loads(json_str)
            
            # Validate required fields
            required_fields = ['status', 'reason', 'confidence', 'detected_elements', 'severity', 'action_recommended']
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Missing required field in response: {field}")
            
            # Validate status
            valid_statuses = ['safe', 'abusive', 'phone_detected', 'policy_violation']
            if result['status'] not in valid_statuses:
                raise ValueError(f"status must be one of: {', '.join(valid_statuses)}")
            
            # Validate confidence
            confidence = result['confidence']
            if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
                raise ValueError("Confidence must be between 0 and 1")
            
            # Validate severity
            valid_severities = ['low', 'medium', 'high']
            if result['severity'] not in valid_severities:
                raise ValueError(f"severity must be one of: {', '.join(valid_severities)}")
            
            # Validate action
            valid_actions = ['none', 'warn', 'block', 'review']
            if result['action_recommended'] not in valid_actions:
                raise ValueError(f"action_recommended must be one of: {', '.join(valid_actions)}")
            
            # Ensure detected_elements is a list
            if not isinstance(result['detected_elements'], list):
                result['detected_elements'] = [str(result['detected_elements'])]
            
            return result
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {str(e)}")
            raise ValueError("Invalid JSON response from LLM")
        except Exception as e:
            self.logger.error(f"Error parsing response: {str(e)}")
            raise ValueError(f"Failed to parse response: {str(e)}")
