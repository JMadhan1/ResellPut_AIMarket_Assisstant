from abc import ABC, abstractmethod
import logging
import time
from typing import Dict, Any, Optional
from utils.llm_client import LLMClientFactory

class BaseAgent(ABC):
    """Abstract base class for all marketplace agents"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.execution_count = 0
        self.success_count = 0
        self.total_processing_time = 0.0
        self.llm_client = LLMClientFactory.create_client()

    @abstractmethod
    def _generate_prompt(self, data: Dict[str, Any]) -> str:
        """Generate the prompt for the LLM based on input data"""
        pass

    @abstractmethod
    def _validate_input(self, data: Dict[str, Any]) -> None:
        """Validate input data before processing"""
        pass

    @abstractmethod
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse and validate the LLM response"""
        pass

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Main processing method with error handling and statistics tracking"""
        start_time = time.time()
        self.execution_count += 1

        try:
            # Validate input
            self._validate_input(data)

            # Generate prompt
            prompt = self._generate_prompt(data)
            self.logger.debug(f"Generated prompt: {prompt[:200]}...")

            # Call LLM with retry logic
            response = self._call_llm_with_retry(prompt)
            self.logger.debug(f"LLM response: {response[:200]}...")

            # Parse response
            result = self._parse_response(response)

            # Update success statistics
            self.success_count += 1
            processing_time = time.time() - start_time
            self.total_processing_time += processing_time

            self.logger.info(f"Successfully processed request in {processing_time:.2f}s")

            # Add metadata
            result['metadata'] = {
                'processing_time': processing_time,
                'agent_type': self.__class__.__name__,
                'execution_id': self.execution_count
            }

            return result

        except Exception as e:
            processing_time = time.time() - start_time
            self.total_processing_time += processing_time
            self.logger.error(f"Error processing request: {str(e)}")
            raise

    def _call_llm_with_retry(self, prompt: str, max_retries: int = 2) -> str:
        """Call LLM with retry logic"""
        last_exception = None

        for attempt in range(max_retries):
            try:
                response = self.llm_client.generate(prompt)
                if response and response.strip():
                    return response
                else:
                    raise ValueError("Empty response from LLM")
            except Exception as e:
                last_exception = e
                self.logger.warning(f"LLM call attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(1)  # Shorter wait time

        raise last_exception

    def _update_stats(self, success: bool, processing_time: float):
        """Update agent statistics"""
        self.execution_count += 1
        self.total_processing_time += processing_time
        if success:
            self.success_count += 1


    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.execution_count == 0:
            return 0.0
        return self.success_count / self.execution_count

    @property
    def avg_processing_time(self) -> float:
        """Calculate average processing time"""
        if self.execution_count == 0:
            return 0.0
        return self.total_processing_time / self.execution_count

    def get_statistics(self) -> Dict[str, Any]:
        """Get agent statistics"""
        return {
            'execution_count': self.execution_count,
            'success_count': self.success_count,
            'success_rate': self.success_rate,
            'avg_processing_time': self.avg_processing_time,
            'total_processing_time': self.total_processing_time
        }