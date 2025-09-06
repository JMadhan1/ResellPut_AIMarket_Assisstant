# Resellpur AI Assistant

## Overview

This is an AI-powered marketplace assistant built for Resellpur that provides two main services: intelligent price suggestions and chat moderation. The application uses Flask as the web framework and integrates with multiple LLM providers (Groq, Hugging Face) to deliver AI-powered features for marketplace operations.

The system helps sellers get optimal pricing recommendations based on market data analysis and provides automated chat moderation to maintain platform quality and safety.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Technology**: HTML5, CSS3, JavaScript with Bootstrap 5 for responsive UI
- **Design Pattern**: Single-page application with AJAX for asynchronous API calls
- **Components**: 
  - Price suggestion form with product details input
  - Chat moderation interface for message analysis
  - Real-time system status monitoring
  - Loading modals and result displays

### Backend Architecture
- **Framework**: Flask web application with modular structure
- **Design Pattern**: Agent-based architecture with inheritance hierarchy
- **Core Components**:
  - `BaseAgent`: Abstract base class providing common functionality (logging, validation, LLM integration)
  - `PriceSuggestorAgent`: Handles price analysis using market data and depreciation algorithms
  - `ChatModeratorAgent`: Processes messages for spam, abuse, and policy violations
  - `DataProcessor`: Manages marketplace data loading, cleaning, and analysis
  - `LLMClientFactory`: Abstraction layer for multiple LLM providers

### Data Processing
- **Storage**: CSV-based marketplace data with fallback data generation
- **Processing**: Pandas for data manipulation and analysis
- **Algorithms**: 
  - Depreciation calculations based on product category and age
  - Brand value multipliers for premium brands
  - Location-based price adjustments
  - Statistical analysis for price recommendations

### LLM Integration
- **Provider Support**: Groq API (primary), Hugging Face API, Mock client for testing
- **Models**: Mixtral-8x7b-32768 (Groq), Mistral-7B-Instruct (HuggingFace)
- **Features**: Retry logic, response parsing, JSON extraction utilities
- **Fallback**: Graceful degradation with mock responses when APIs are unavailable

### Agent System
- **Base Agent**: Common functionality including execution tracking, error handling, input validation
- **Price Suggestor**: 
  - Market data analysis with category-specific depreciation rates
  - Brand and location multipliers for accurate pricing
  - Condition-based adjustments
  - LLM-powered contextual analysis
- **Chat Moderator**:
  - Pattern matching for phone numbers, spam keywords
  - External platform detection
  - LLM-powered content analysis for policy violations
  - Real-time moderation scoring

### API Design
- **RESTful Endpoints**: Health checks, statistics, price negotiation, chat moderation
- **Error Handling**: Comprehensive exception handling with proper HTTP status codes
- **Logging**: Structured logging throughout the application
- **Validation**: Input validation at multiple layers (frontend, agent, base classes)

## External Dependencies

### LLM Services
- **Groq API**: Primary LLM provider for fast inference using Mixtral model
- **Hugging Face API**: Secondary provider with Mistral-7B-Instruct model
- **Configuration**: API keys managed through environment variables

### Python Libraries
- **Flask**: Web framework for API and web interface
- **Pandas**: Data processing and analysis
- **Requests**: HTTP client for LLM API calls
- **Logging**: Built-in Python logging for monitoring and debugging

### Frontend Libraries
- **Bootstrap 5**: UI framework for responsive design
- **Feather Icons**: Icon library for consistent UI elements
- **Native JavaScript**: For AJAX calls and DOM manipulation

### Development Tools
- **Environment Variables**: Configuration management for API keys and secrets
- **CSV Data Storage**: Simple file-based data persistence
- **Error Recovery**: Fallback mechanisms for API failures and missing data