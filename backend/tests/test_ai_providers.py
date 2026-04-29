"""Tests for AI Providers Module

Comprehensive tests for the pluggable AI architecture.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

# Import AI provider modules
from ai_providers import (
    BaseAIProvider, 
    AIResponse, 
    AIProviderFactory,
    GeminiProvider,
    GroqProvider,
    OpenAIRouterProvider
)
from ai_providers.exceptions import (
    AIProviderError,
    ProviderInitializationError,
    ModelNotSupportedError,
    ContentGenerationError
)
from ai_service import AIService


class TestAIResponse:
    """Test AIResponse model."""
    
    def test_ai_response_creation(self):
        """Test creating an AI response."""
        response = AIResponse(
            content="Hello world",
            model="test-model",
            provider="test-provider",
            usage={"tokens": 10},
            metadata={"temperature": 0.7}
        )
        
        assert response.content == "Hello world"
        assert response.model == "test-model"
        assert response.provider == "test-provider"
        assert response.usage["tokens"] == 10
        assert response.metadata["temperature"] == 0.7


class MockAIProvider(BaseAIProvider):
    """Mock AI provider for testing."""
    
    @property
    def provider_name(self) -> str:
        return "mock"
    
    @property
    def supported_models(self) -> list[str]:
        return ["mock-model-1", "mock-model-2"]
    
    async def initialize(self) -> None:
        self._client = Mock()
    
    async def generate_content(self, prompt: str, model: str = None, **kwargs) -> AIResponse:
        if not model:
            model = self.get_default_model()
        
        return AIResponse(
            content=f"Mock response to: {prompt}",
            model=model,
            provider=self.provider_name,
            usage={"tokens": len(prompt)},
            metadata=kwargs
        )
    
    async def health_check(self) -> bool:
        return True


class TestBaseAIProvider:
    """Test base AI provider functionality."""
    
    @pytest.fixture
    def mock_provider(self):
        return MockAIProvider(api_key="test-key")
    
    def test_provider_initialization(self, mock_provider):
        """Test provider initialization."""
        assert mock_provider.api_key == "test-key"
        assert mock_provider.provider_name == "mock"
        assert "mock-model-1" in mock_provider.supported_models
    
    def test_get_default_model(self, mock_provider):
        """Test getting default model."""
        default_model = mock_provider.get_default_model()
        assert default_model == "mock-model-1"
    
    @pytest.mark.asyncio
    async def test_async_context_manager(self, mock_provider):
        """Test async context manager."""
        async with mock_provider as provider:
            assert provider._client is not None
    
    @pytest.mark.asyncio
    async def test_generate_content(self, mock_provider):
        """Test content generation."""
        await mock_provider.initialize()
        
        response = await mock_provider.generate_content(
            prompt="Test prompt",
            temperature=0.8
        )
        
        assert response.content == "Mock response to: Test prompt"
        assert response.provider == "mock"
        assert response.metadata["temperature"] == 0.8


class TestAIProviderFactory:
    """Test AI provider factory."""
    
    def test_create_supported_provider(self):
        """Test creating a supported provider."""
        provider = AIProviderFactory.create_provider(
            provider_type="gemini",
            api_key="test-key"
        )
        
        assert isinstance(provider, GeminiProvider)
        assert provider.api_key == "test-key"
    
    def test_create_unsupported_provider(self):
        """Test creating an unsupported provider."""
        with pytest.raises(ValueError, match="Unsupported provider type"):
            AIProviderFactory.create_provider(
                provider_type="unsupported",
                api_key="test-key"
            )
    
    def test_get_supported_providers(self):
        """Test getting supported providers."""
        providers = AIProviderFactory.get_supported_providers()
        
        assert "gemini" in providers
        assert "groq" in providers
        assert "openai_router" in providers
    
    def test_register_provider(self):
        """Test registering a new provider."""
        AIProviderFactory.register_provider("mock", MockAIProvider)
        
        provider = AIProviderFactory.create_provider(
            provider_type="mock",
            api_key="test-key"
        )
        
        assert isinstance(provider, MockAIProvider)


class TestAIService:
    """Test AI service functionality."""
    
    @pytest.fixture
    def ai_service(self):
        return AIService()
    
    @pytest.mark.asyncio
    async def test_add_provider(self, ai_service):
        """Test adding a provider."""
        with patch.object(MockAIProvider, 'initialize', new_callable=AsyncMock):
            await ai_service.add_provider(
                name="test_provider",
                provider_type="mock",
                api_key="test-key",
                is_default=True
            )
        
        assert "test_provider" in ai_service.list_providers()
        assert ai_service.get_default_provider_name() == "test_provider"
    
    @pytest.mark.asyncio
    async def test_remove_provider(self, ai_service):
        """Test removing a provider."""
        # First add a provider
        with patch.object(MockAIProvider, 'initialize', new_callable=AsyncMock):
            await ai_service.add_provider(
                name="test_provider",
                provider_type="mock",
                api_key="test-key"
            )
        
        # Then remove it
        await ai_service.remove_provider("test_provider")
        
        assert "test_provider" not in ai_service.list_providers()
    
    @pytest.mark.asyncio
    async def test_generate_content(self, ai_service):
        """Test content generation through service."""
        # Register mock provider
        AIProviderFactory.register_provider("mock", MockAIProvider)
        
        with patch.object(MockAIProvider, 'initialize', new_callable=AsyncMock):
            await ai_service.add_provider(
                name="test_provider",
                provider_type="mock",
                api_key="test-key"
            )
        
        response = await ai_service.generate_content(
            prompt="Test prompt",
            provider_name="test_provider"
        )
        
        assert "Test prompt" in response.content
        assert response.provider == "mock"
    
    @pytest.mark.asyncio
    async def test_health_check(self, ai_service):
        """Test health check functionality."""
        AIProviderFactory.register_provider("mock", MockAIProvider)
        
        with patch.object(MockAIProvider, 'initialize', new_callable=AsyncMock):
            await ai_service.add_provider(
                name="test_provider",
                provider_type="mock",
                api_key="test-key"
            )
        
        health = await ai_service.health_check()
        
        assert "test_provider" in health
        assert health["test_provider"] is True
    
    def test_get_nonexistent_provider(self, ai_service):
        """Test getting a non-existent provider."""
        with pytest.raises(ValueError, match="Provider 'nonexistent' not found"):
            ai_service.get_provider("nonexistent")
    
    @pytest.mark.asyncio
    async def test_provider_context(self, ai_service):
        """Test provider context manager."""
        AIProviderFactory.register_provider("mock", MockAIProvider)
        
        with patch.object(MockAIProvider, 'initialize', new_callable=AsyncMock):
            await ai_service.add_provider(
                name="test_provider",
                provider_type="mock",
                api_key="test-key"
            )
        
        async with ai_service.provider_context("test_provider") as provider:
            assert isinstance(provider, MockAIProvider)


class TestGeminiProvider:
    """Test Gemini provider specific functionality."""
    
    def test_provider_properties(self):
        """Test Gemini provider properties."""
        provider = GeminiProvider(api_key="test-key")
        
        assert provider.provider_name == "gemini"
        assert "gemini-2.5-pro" in provider.supported_models
        assert "gemini-1.5-pro" in provider.supported_models
    
    def test_unsupported_model(self):
        """Test using unsupported model."""
        provider = GeminiProvider(api_key="test-key")
        
        with pytest.raises(ValueError, match="Model unsupported-model not supported"):
            asyncio.run(provider.generate_content(
                prompt="test",
                model="unsupported-model"
            ))


class TestGroqProvider:
    """Test Groq provider specific functionality."""
    
    def test_provider_properties(self):
        """Test Groq provider properties."""
        provider = GroqProvider(api_key="test-key")
        
        assert provider.provider_name == "groq"
        assert "llama-3.3-70b-versatile" in provider.supported_models
        assert "mixtral-8x7b-32768" in provider.supported_models


class TestOpenAIRouterProvider:
    """Test OpenAI Router provider specific functionality."""
    
    def test_provider_properties(self):
        """Test OpenAI Router provider properties."""
        provider = OpenAIRouterProvider(api_key="test-key")
        
        assert provider.provider_name == "openai_router"
        assert "anthropic/claude-3.5-sonnet" in provider.supported_models
        assert "openai/gpt-4o" in provider.supported_models


class TestErrorHandling:
    """Test error handling scenarios."""
    
    @pytest.mark.asyncio
    async def test_provider_initialization_error(self):
        """Test provider initialization error."""
        ai_service = AIService()
        
        with patch.object(MockAIProvider, 'initialize', side_effect=Exception("Init failed")):
            with pytest.raises(ProviderInitializationError):
                await ai_service.add_provider(
                    name="failing_provider",
                    provider_type="mock",
                    api_key="test-key"
                )
    
    @pytest.mark.asyncio
    async def test_content_generation_error(self, ai_service):
        """Test content generation error."""
        AIProviderFactory.register_provider("mock", MockAIProvider)
        
        with patch.object(MockAIProvider, 'initialize', new_callable=AsyncMock):
            await ai_service.add_provider(
                name="test_provider",
                provider_type="mock",
                api_key="test-key"
            )
        
        with patch.object(MockAIProvider, 'generate_content', side_effect=Exception("Generation failed")):
            with pytest.raises(ContentGenerationError):
                await ai_service.generate_content(
                    prompt="Test prompt",
                    provider_name="test_provider"
                )


if __name__ == "__main__":
    pytest.main([__file__])
