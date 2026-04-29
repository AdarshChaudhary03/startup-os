import asyncio
import logging
from content_writer_v2.main_agent import ContentWriterMainAgent
from content_writer_v2.config import DEFAULT_CONFIG

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_content_writer_v2():
    """Test Content Writer v2 directly to verify Instagram caption generation."""
    
    try:
        print("=== Testing Content Writer v2 Direct ===\n")
        
        # Create main agent
        print("1. Creating Content Writer v2 Main Agent...")
        main_agent = ContentWriterMainAgent(DEFAULT_CONFIG)
        
        # Initialize agent
        print("2. Initializing agent...")
        await main_agent.initialize()
        print("   Agent initialized successfully!\n")
        
        # Test Instagram caption generation
        task = "Write an instagram caption for a sunny Day in Delhi"
        request_id = "test_instagram_caption_001"
        
        print(f"3. Testing task: {task}")
        print(f"   Request ID: {request_id}\n")
        
        # Generate content
        print("4. Generating content...")
        result = await main_agent.generate_content(
            task=task,
            request_id=request_id
        )
        
        print("5. Content generation completed!\n")
        
        # Display results
        print("=== RESULTS ===")
        print(f"Category Used: {result.get('category_used', 'unknown')}")
        print(f"Sub-Agent Used: {result.get('sub_agent_used', 'unknown')}")
        print(f"Content Length: {len(result.get('content', ''))} characters")
        print(f"\nGenerated Content:")
        print("-" * 50)
        print(result.get('content', 'No content generated'))
        print("-" * 50)
        
        # Display metadata if available
        if 'metadata' in result:
            print(f"\nMetadata:")
            metadata = result['metadata']
            for key, value in metadata.items():
                print(f"  {key}: {value}")
        
        # Display hashtags if available
        if 'hashtags' in result:
            print(f"\nHashtags: {', '.join(result['hashtags'])}")
        
        # Display validation if available
        if 'validation' in result:
            validation = result['validation']
            print(f"\nValidation:")
            print(f"  Within Limit: {validation.get('within_limit', 'unknown')}")
            print(f"  Character Count: {validation.get('character_count', 'unknown')}")
            print(f"  Platform Limit: {validation.get('platform_limit', 'unknown')}")
        
        print("\n=== TEST COMPLETED SUCCESSFULLY ===")
        
    except Exception as e:
        print(f"\nERROR: Content Writer v2 test failed: {e}")
        logger.error(f"Content Writer v2 test failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    asyncio.run(test_content_writer_v2())
