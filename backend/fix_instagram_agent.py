#!/usr/bin/env python3
"""
Fix Instagram Agent Implementation
This script updates the Instagram agent to use proper image URLs and fix API integration.
"""

import os
import sys

def update_instagram_agent():
    """Update Instagram agent with proper image URL handling"""
    
    instagram_agent_path = "social_media_publisher/sub_agents/instagram.py"
    
    # Read current content
    try:
        with open(instagram_agent_path, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"❌ File not found: {instagram_agent_path}")
        return False
    
    # Define the new image URL handling logic
    new_image_logic = '''    def _get_default_image_url(self) -> str:
        """Get a reliable default image URL for Instagram posting."""
        # Use a reliable, publicly accessible image URL
        # This should be replaced with your own hosted image
        reliable_images = [
            "https://cdn.pixabay.com/photo/2015/04/23/22/00/tree-736885_1280.jpg",
            "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1080&h=1080&fit=crop&auto=format",
            "https://raw.githubusercontent.com/microsoft/vscode/main/resources/linux/code.png"
        ]
        
        # Test each URL and return the first working one
        import requests
        for url in reliable_images:
            try:
                response = requests.head(url, timeout=5)
                if response.status_code == 200 and 'image/' in response.headers.get('content-type', ''):
                    logger.info(f"Using reliable image URL: {url}")
                    return url
            except:
                continue
        
        # Fallback to first URL if testing fails
        return reliable_images[0]'''
    
    # Replace the problematic picsum.photos URL
    updated_content = content.replace(
        'https://picsum.photos/1080/1080?random=1',
        'self._get_default_image_url()'
    )
    
    # Add the new method before the existing methods
    if '_get_default_image_url' not in updated_content:
        # Find a good place to insert the method
        insert_point = updated_content.find('    async def _publish_post(')
        if insert_point != -1:
            updated_content = (
                updated_content[:insert_point] + 
                new_image_logic + '\n\n' +
                updated_content[insert_point:]
            )
    
    # Write updated content
    try:
        with open(instagram_agent_path, 'w') as f:
            f.write(updated_content)
        print(f"✅ Updated {instagram_agent_path}")
        return True
    except Exception as e:
        print(f"❌ Error updating file: {e}")
        return False

def main():
    """Main function"""
    print("🔧 Fixing Instagram Agent Implementation")
    print("======================================")
    
    if update_instagram_agent():
        print("\n✅ Instagram agent updated successfully!")
        print("\n📋 Next steps:")
        print("1. Run: python3 test_instagram_curl.py")
        print("2. Test with: bash run_instagram_test.sh")
        print("3. Check logs for any remaining issues")
    else:
        print("\n❌ Failed to update Instagram agent")

if __name__ == "__main__":
    main()
