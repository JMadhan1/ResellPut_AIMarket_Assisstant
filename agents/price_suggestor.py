import json
import logging
from typing import Dict, Any
from agents.base_agent import BaseAgent
from utils.data_processor import DataProcessor
import time
import uuid

class PriceSuggestorAgent(BaseAgent):
    """Agent for intelligent price suggestions based on marketplace data"""

    def __init__(self):
        super().__init__()
        self.data_processor = DataProcessor()

        # Depreciation rates by category (per month)
        self.depreciation_rates = {
            'Mobile': 0.05,      # 5% per month
            'Laptop': 0.04,      # 4% per month
            'Electronics': 0.03,  # 3% per month
            'Camera': 0.02,      # 2% per month
            'Fashion': 0.08,     # 8% per month
            'Furniture': 0.01,   # 1% per month
        }

        # Brand value retention multipliers
        self.brand_multipliers = {
            'Apple': 1.2,
            'Samsung': 1.1,
            'Sony': 1.1,
            'Canon': 1.1,
            'Nike': 1.05,
            'Adidas': 1.05,
            'default': 1.0
        }

        # Location price adjustments (multipliers)
        self.location_multipliers = {
            'Mumbai': 1.15,
            'Delhi': 1.10,
            'Bangalore': 1.12,
            'Chennai': 1.08,
            'Pune': 1.06,
            'Hyderabad': 1.04,
            'default': 1.0
        }

    def _validate_input(self, data: Dict[str, Any]) -> None:
        """Validate price suggestor input"""
        required_fields = ['title', 'category', 'brand', 'condition', 'age_months', 'asking_price', 'location']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        # Validate data types
        if not isinstance(data['age_months'], (int, float)) or data['age_months'] < 0:
            raise ValueError("age_months must be a non-negative number")

        if not isinstance(data['asking_price'], (int, float)) or data['asking_price'] <= 0:
            raise ValueError("asking_price must be a positive number")

        # Validate condition
        valid_conditions = ['Like New', 'Good', 'Fair']
        if data['condition'] not in valid_conditions:
            raise ValueError(f"condition must be one of: {', '.join(valid_conditions)}")

    def _generate_prompt(self, data: Dict[str, Any]) -> str:
        """Generate pricing prompt with market analysis"""
        try:
            # Get market analysis
            market_analysis = self._analyze_market(data)

            prompt = f"""You are an expert second-hand marketplace pricing analyst with 10+ years of experience.

PRODUCT TO PRICE:
- Item: {data['title']}
- Category: {data['category']}
- Brand: {data['brand']}
- Condition: {data['condition']}
- Age: {data['age_months']} months
- Current asking: ₹{data['asking_price']}
- Location: {data['location']}

MARKET INTELLIGENCE:
- Similar items found: {len(market_analysis['similar_items'])}
- Average price: ₹{market_analysis['avg_price']:.0f}
- Price range: ₹{market_analysis['min_price']:.0f} - ₹{market_analysis['max_price']:.0f}
- Category depreciation rate: {market_analysis['depreciation_rate']}%/month
- Location multiplier: {market_analysis['location_multiplier']:.2f}
- Brand multiplier: {market_analysis['brand_multiplier']:.2f}

PRICING RULES:
1. Like New: 10-20% depreciation from retail
2. Good: 25-40% depreciation from retail
3. Fair: 45-60% depreciation from retail
4. Apply monthly depreciation based on age
5. Consider brand value retention
6. Factor in location premium/discount

Based on this analysis, provide ONLY a JSON response with this exact structure:
{{
    "suggested_price_range": {{
        "min": <minimum_fair_price>,
        "max": <maximum_fair_price>
    }},
    "reasoning": "<detailed_explanation_with_calculations>",
    "confidence": <0.0_to_1.0>,
    "market_position": "<underpriced|fairly_priced|overpriced>",
    "recommendations": ["<actionable_advice>"]
}}"""

            return prompt

        except Exception as e:
            self.logger.error(f"Error generating prompt: {str(e)}")
            # Fallback prompt without market analysis
            return self._generate_fallback_prompt(data)

    def _generate_fallback_prompt(self, data: Dict[str, Any]) -> str:
        """Generate fallback prompt when market analysis fails"""
        return f"""You are an expert second-hand marketplace pricing analyst.

PRODUCT TO PRICE:
- Item: {data['title']}
- Category: {data['category']}
- Brand: {data['brand']}
- Condition: {data['condition']}
- Age: {data['age_months']} months
- Current asking: ₹{data['asking_price']}
- Location: {data['location']}

Analyze this product and provide fair pricing based on general market knowledge.

Provide ONLY a JSON response with this exact structure:
{{
    "suggested_price_range": {{
        "min": <minimum_fair_price>,
        "max": <maximum_fair_price>
    }},
    "reasoning": "<detailed_explanation>",
    "confidence": <0.0_to_1.0>,
    "market_position": "<underpriced|fairly_priced|overpriced>",
    "recommendations": ["<actionable_advice>"]
}}"""

    def _analyze_market(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market data for similar products"""
        try:
            # Load data if not already loaded
            df = self.data_processor.load_data()

            # Find similar products
            similar_items = self.data_processor.find_similar_products(
                data['category'], data['brand'], data['age_months']
            )

            if similar_items.empty:
                # Fallback to category-only matching
                similar_items = df[df['category'] == data['category']]

            # Calculate statistics
            avg_price = similar_items['asking_price'].mean() if not similar_items.empty else data['asking_price']
            min_price = similar_items['asking_price'].min() if not similar_items.empty else data['asking_price'] * 0.8
            max_price = similar_items['asking_price'].max() if not similar_items.empty else data['asking_price'] * 1.2

            # Get depreciation rate
            depreciation_rate = self.depreciation_rates.get(data['category'], 0.03) * 100

            # Get multipliers
            brand_multiplier = self.brand_multipliers.get(data['brand'], self.brand_multipliers['default'])
            location_multiplier = self.location_multipliers.get(data['location'], self.location_multipliers['default'])

            return {
                'similar_items': similar_items.to_dict('records') if not similar_items.empty else [],
                'avg_price': avg_price,
                'min_price': min_price,
                'max_price': max_price,
                'depreciation_rate': depreciation_rate,
                'brand_multiplier': brand_multiplier,
                'location_multiplier': location_multiplier
            }

        except Exception as e:
            self.logger.error(f"Error in market analysis: {str(e)}")
            # Return fallback analysis
            return {
                'similar_items': [],
                'avg_price': data['asking_price'],
                'min_price': data['asking_price'] * 0.8,
                'max_price': data['asking_price'] * 1.2,
                'depreciation_rate': 3.0,
                'brand_multiplier': 1.0,
                'location_multiplier': 1.0
            }

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse and validate LLM response"""
        try:
            # Extract JSON from response
            json_str = self.llm_client.extract_json(response)
            result = json.loads(json_str)

            # Validate required fields
            required_fields = ['suggested_price_range', 'reasoning', 'confidence', 'market_position', 'recommendations']
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Missing required field in response: {field}")

            # Validate price range structure
            price_range = result['suggested_price_range']
            if not isinstance(price_range, dict) or 'min' not in price_range or 'max' not in price_range:
                raise ValueError("Invalid price range structure")

            # Validate confidence score
            confidence = result['confidence']
            if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
                raise ValueError("Confidence must be between 0 and 1")

            # Validate market position
            valid_positions = ['underpriced', 'fairly_priced', 'overpriced']
            if result['market_position'] not in valid_positions:
                raise ValueError(f"market_position must be one of: {', '.join(valid_positions)}")

            return result

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {str(e)}")
            raise ValueError("Invalid JSON response from LLM")
        except Exception as e:
            self.logger.error(f"Error parsing response: {str(e)}")
            raise ValueError(f"Failed to parse response: {str(e)}")

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process price suggestion request"""
        start_time = time.time()

        try:
            # Validate input
            self._validate_input(data)

            # Generate prompt
            prompt = self._generate_prompt(data)
            self.logger.debug(f"Generated prompt: {prompt[:200]}...")

            # Get LLM response with retries
            response = self._call_llm_with_retry(prompt)

            # Parse response
            result = self._parse_response(response)

            # Add fraud detection
            fraud_analysis = self._detect_fraud_indicators(data)
            result['fraud_analysis'] = fraud_analysis

            # Enhance confidence with market analysis
            market_analysis = self._analyze_market(data)
            enhanced_confidence = self._calculate_confidence_score(data, market_analysis)
            result['confidence'] = max(result.get('confidence', 0), enhanced_confidence)

            # Add metadata
            processing_time = time.time() - start_time
            result['metadata'] = {
                'processing_time': processing_time,
                'agent_type': 'price_suggestor',
                'execution_id': str(uuid.uuid4())
            }

            # Update statistics
            self._update_stats(True, processing_time)

            self.logger.info(f"Successfully processed price suggestion in {processing_time:.2f}s")
            return result

        except Exception as e:
            processing_time = time.time() - start_time
            self._update_stats(False, processing_time)
            self.logger.error(f"Error processing request: {str(e)}")

            # Always provide fallback pricing when LLM fails
            self.logger.info("LLM failed, using mathematical fallback pricing")
            try:
                return self._generate_fallback_pricing(data, processing_time)
            except Exception as fallback_error:
                self.logger.error(f"Fallback pricing also failed: {str(fallback_error)}")
                # Ultimate emergency fallback
                return {
                    'suggested_price_range': {
                        'min': int(data['asking_price'] * 0.8),
                        'max': int(data['asking_price'] * 1.2)
                    },
                    'reasoning': "AI analysis temporarily unavailable. Showing basic estimate based on your asking price.",
                    'confidence': 0.3,
                    'market_position': "fairly_priced",
                    'recommendations': ["Our AI systems are being optimized. Try again in a few minutes for detailed analysis."],
                    'metadata': {
                        'processing_time': processing_time,
                        'agent_type': 'emergency_fallback',
                        'execution_id': str(uuid.uuid4())
                    }
                }

    def _detect_fraud_indicators(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect potential fraud indicators in pricing data"""
        fraud_score = 0.0
        fraud_indicators = []
        
        try:
            asking_price = data['asking_price']
            age_months = data['age_months']
            category = data['category']
            
            # Load market data for comparison
            df = self.data_processor.load_data()
            similar_items = df[df['category'] == category]
            
            if not similar_items.empty:
                avg_price = similar_items['asking_price'].mean()
                price_std = similar_items['asking_price'].std()
                
                # Check for extremely low pricing (potential scam)
                if asking_price < (avg_price - 2 * price_std):
                    fraud_score += 0.3
                    fraud_indicators.append("Suspiciously low price compared to market average")
                
                # Check for extremely high pricing (potential overpricing)
                if asking_price > (avg_price + 3 * price_std):
                    fraud_score += 0.2
                    fraud_indicators.append("Significantly overpriced compared to market")
            
            # Check for unrealistic age
            if age_months > 120:  # More than 10 years
                fraud_score += 0.1
                fraud_indicators.append("Unusually old product age")
            
            # Check for brand-price mismatch
            if data['brand'] in ['Apple', 'Samsung'] and asking_price < 5000:
                fraud_score += 0.4
                fraud_indicators.append("Premium brand with suspiciously low price")
            
            # Check for condition-price mismatch
            if data['condition'] == 'Like New' and age_months > 36:
                fraud_score += 0.2
                fraud_indicators.append("'Like New' condition inconsistent with age")
            
            return {
                'fraud_score': min(fraud_score, 1.0),
                'fraud_indicators': fraud_indicators,
                'risk_level': 'high' if fraud_score > 0.6 else 'medium' if fraud_score > 0.3 else 'low'
            }
            
        except Exception as e:
            self.logger.error(f"Fraud detection failed: {str(e)}")
            return {
                'fraud_score': 0.0,
                'fraud_indicators': [],
                'risk_level': 'low'
            }

    def _calculate_confidence_score(self, data: Dict[str, Any], market_analysis: Dict[str, Any]) -> float:
        """Calculate confidence score for price suggestion"""
        confidence = 0.5  # Base confidence
        
        try:
            # Market data availability
            similar_items_count = len(market_analysis.get('similar_items', []))
            if similar_items_count > 10:
                confidence += 0.3
            elif similar_items_count > 5:
                confidence += 0.2
            elif similar_items_count > 0:
                confidence += 0.1
            
            # Brand recognition
            if data['brand'] in self.brand_multipliers:
                confidence += 0.1
            
            # Age reasonableness
            if 0 <= data['age_months'] <= 60:  # 0-5 years
                confidence += 0.1
            
            # Data completeness
            required_fields = ['title', 'category', 'brand', 'condition', 'age_months', 'asking_price', 'location']
            if all(field in data and data[field] for field in required_fields):
                confidence += 0.1
            
            return min(confidence, 1.0)
            
        except Exception as e:
            self.logger.error(f"Confidence calculation failed: {str(e)}")
            return 0.5

    def _generate_fallback_pricing(self, data: Dict[str, Any], processing_time: float) -> Dict[str, Any]:
        """Generate basic price estimate when LLM is unavailable"""
        try:
            asking_price = data['asking_price']
            age_months = data['age_months']
            category = data['category']
            condition = data['condition']

            # Basic depreciation calculation
            depreciation_rate = self.depreciation_rates.get(category, 0.03)
            brand_multiplier = self.brand_multipliers.get(data['brand'], 1.0)
            location_multiplier = self.location_multipliers.get(data['location'], 1.0)

            # Condition multipliers
            condition_multipliers = {
                'Like New': 0.85,
                'Good': 0.70,
                'Fair': 0.55
            }
            condition_multiplier = condition_multipliers.get(condition, 0.70)

            # Calculate depreciated value
            monthly_depreciation = 1 - depreciation_rate
            depreciated_value = asking_price * (monthly_depreciation ** age_months)

            # Apply condition and brand adjustments
            estimated_value = depreciated_value * condition_multiplier * brand_multiplier * location_multiplier

            # Create price range (±15%)
            min_price = int(estimated_value * 0.85)
            max_price = int(estimated_value * 1.15)

            # Determine market position
            if asking_price < min_price:
                market_position = "underpriced"
            elif asking_price > max_price:
                market_position = "overpriced"
            else:
                market_position = "fairly_priced"

            return {
                'suggested_price_range': {
                    'min': min_price,
                    'max': max_price
                },
                'reasoning': f"Based on mathematical analysis: {condition} condition {category} from {data['brand']} with {age_months} months of age. Applied {depreciation_rate*100:.1f}% monthly depreciation, {condition_multiplier*100:.0f}% condition adjustment, and location factor for {data['location']}.",
                'confidence': 0.6,  # Lower confidence for fallback
                'market_position': market_position,
                'recommendations': [
                    f"Consider pricing between ₹{min_price:,} - ₹{max_price:,}",
                    "Note: This is a basic estimate. Full AI analysis temporarily unavailable."
                ],
                'metadata': {
                    'processing_time': processing_time,
                    'agent_type': 'price_suggestor_fallback',
                    'execution_id': str(uuid.uuid4())
                }
            }

        except Exception as e:
            self.logger.error(f"Fallback pricing failed: {str(e)}")
            # Ultimate fallback
            return {
                'suggested_price_range': {
                    'min': int(data['asking_price'] * 0.8),
                    'max': int(data['asking_price'] * 1.2)
                },
                'reasoning': "Unable to perform detailed analysis. Showing basic range around your asking price.",
                'confidence': 0.3,
                'market_position': "fairly_priced",
                'recommendations': ["Please try again later for detailed AI analysis"],
                'metadata': {
                    'processing_time': processing_time,
                    'agent_type': 'price_suggestor_emergency',
                    'execution_id': str(uuid.uuid4())
                }
            }