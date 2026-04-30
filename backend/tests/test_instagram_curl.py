#!/usr/bin/env python3
"""
Instagram API Testing Script with cURL Examples
This script provides comprehensive testing for Instagram Graph API integration.
"""

import requests
import json
import os
from typing import Dict, Any, Optional
import time

class InstagramAPITester:
    def __init__(self):
        self.access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN', 'EAAaaZBVbXxHkBRRmKJPRSkGS2RMDnRCoVqA0f3qwjZACnZAfD8ikv2jFWZAG4MSY4lbdqkPPZBvJce1Y5ctfL8olenkkNaCgUDGWoaDY6NtQwxoOwoiwDvqntCBRVtIrIlvDJ5FBA7st17HZCG3TQIWVMyIEmRKuiyxmfPCVRtGfNL8HdUh3gTM5Q8ZAmK3mwZDZD')
        self.ig_user_id = os.getenv('INSTAGRAM_USER_ID', '17841439653964722')
        self.base_url = 'https://graph.facebook.com/v18.0'
        
        # Valid image URLs for testing
        self.test_images = [
            'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1080&h=1080&fit=crop&auto=format',
            'https://cdn.pixabay.com/photo/2015/04/23/22/00/tree-736885_1280.jpg',
            'https://raw.githubusercontent.com/username/repo/main/sample.jpg',  # Replace with actual
        ]
    
    def print_curl_command(self, method: str, url: str, data: Dict = None, headers: Dict = None):
        """Print equivalent cURL command for debugging"""
        curl_cmd = f"curl -X {method} \\
  '{url}'"
        
        if headers:
            for key, value in headers.items():
                curl_cmd += f" \\
  -H '{key}: {value}'"
        
        if data:
            curl_cmd += f" \\
  -d '{json.dumps(data)}'"
        
        print(f"\n📋 Equivalent cURL command:")
        print(curl_cmd)
        print()
    
    def test_access_token(self) -> bool:
        """Test if access token is valid"""
        print("🔑 Testing Access Token...")
        
        url = f"{self.base_url}/me"
        params = {'access_token': self.access_token}
        
        self.print_curl_command('GET', f"{url}?access_token={self.access_token}")
        
        try:
            response = requests.get(url, params=params)
            result = response.json()
            
            if response.status_code == 200:
                print(f"✅ Access token valid for user: {result.get('name', 'Unknown')}")
                return True
            else:
                print(f"❌ Access token invalid: {result}")
                return False
        except Exception as e:
            print(f"❌ Error testing access token: {e}")
            return False
    
    def test_instagram_account(self) -> bool:
        """Test Instagram business account access"""
        print("📱 Testing Instagram Account Access...")
        
        url = f"{self.base_url}/{self.ig_user_id}"
        params = {
            'fields': 'account_type,username,name',
            'access_token': self.access_token
        }
        
        self.print_curl_command('GET', f"{url}?fields=account_type,username,name&access_token={self.access_token}")
        
        try:
            response = requests.get(url, params=params)
            result = response.json()
            
            if response.status_code == 200:
                print(f"✅ Instagram account accessible:")
                print(f"   - Username: {result.get('username', 'N/A')}")
                print(f"   - Account Type: {result.get('account_type', 'N/A')}")
                return True
            else:
                print(f"❌ Instagram account not accessible: {result}")
                return False
        except Exception as e:
            print(f"❌ Error accessing Instagram account: {e}")
            return False
    
    def test_image_url(self, image_url: str) -> bool:
        """Test if image URL is accessible and valid"""
        print(f"🖼️  Testing image URL: {image_url}")
        
        self.print_curl_command('HEAD', image_url)
        
        try:
            response = requests.head(image_url, timeout=10)
            content_type = response.headers.get('content-type', '')
            
            if response.status_code == 200:
                if 'image/' in content_type:
                    print(f"✅ Image URL valid - Content-Type: {content_type}")
                    return True
                else:
                    print(f"❌ Invalid content type: {content_type}")
                    return False
            else:
                print(f"❌ Image URL not accessible - Status: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error testing image URL: {e}")
            return False
    
    def create_media_container(self, image_url: str, caption: str) -> Optional[str]:
        """Create Instagram media container"""
        print(f"📦 Creating media container...")
        
        url = f"{self.base_url}/{self.ig_user_id}/media"
        data = {
            'image_url': image_url,
            'caption': caption,
            'access_token': self.access_token
        }
        
        self.print_curl_command('POST', url, data)
        
        try:
            response = requests.post(url, json=data)
            result = response.json()
            
            print(f"Response Status: {response.status_code}")
            print(f"Response Body: {json.dumps(result, indent=2)}")
            
            if response.status_code == 200 and 'id' in result:
                container_id = result['id']
                print(f"✅ Media container created: {container_id}")
                return container_id
            else:
                print(f"❌ Failed to create media container: {result}")
                return None
        except Exception as e:
            print(f"❌ Error creating media container: {e}")
            return None
    
    def publish_media(self, container_id: str) -> bool:
        """Publish Instagram media"""
        print(f"🚀 Publishing media container: {container_id}")
        
        url = f"{self.base_url}/{self.ig_user_id}/media_publish"
        data = {
            'creation_id': container_id,
            'access_token': self.access_token
        }
        
        self.print_curl_command('POST', url, data)
        
        try:
            response = requests.post(url, json=data)
            result = response.json()
            
            print(f"Response Status: {response.status_code}")
            print(f"Response Body: {json.dumps(result, indent=2)}")
            
            if response.status_code == 200 and 'id' in result:
                media_id = result['id']
                print(f"✅ Media published successfully: {media_id}")
                return True
            else:
                print(f"❌ Failed to publish media: {result}")
                return False
        except Exception as e:
            print(f"❌ Error publishing media: {e}")
            return False
    
    def run_comprehensive_test(self):
        """Run comprehensive Instagram API test"""
        print("🧪 Starting Comprehensive Instagram API Test")
        print("=" * 50)
        
        # Test 1: Access Token
        if not self.test_access_token():
            print("\n❌ Access token test failed. Cannot proceed.")
            return
        
        print("\n" + "-" * 30)
        
        # Test 2: Instagram Account
        if not self.test_instagram_account():
            print("\n❌ Instagram account test failed. Cannot proceed.")
            return
        
        print("\n" + "-" * 30)
        
        # Test 3: Image URLs
        valid_image = None
        for image_url in self.test_images:
            if self.test_image_url(image_url):
                valid_image = image_url
                break
            print()
        
        if not valid_image:
            print("\n❌ No valid image URLs found. Using a default test image.")
            # Use a known working image for testing
            valid_image = "https://cdn.pixabay.com/photo/2015/04/23/22/00/tree-736885_1280.jpg"
        
        print("\n" + "-" * 30)
        
        # Test 4: Create Media Container
        caption = f"Test post from Instagram API - {int(time.time())}"
        container_id = self.create_media_container(valid_image, caption)
        
        if not container_id:
            print("\n❌ Media container creation failed.")
            return
        
        print("\n" + "-" * 30)
        
        # Test 5: Publish Media (Optional - uncomment to actually post)
        print("\n⚠️  READY TO PUBLISH TO INSTAGRAM")
        print("Uncomment the next lines to actually post to Instagram:")
        print("# if self.publish_media(container_id):")
        print("#     print('🎉 Instagram post published successfully!')")
        print("# else:")
        print("#     print('❌ Failed to publish Instagram post')")
        
        # Uncomment these lines to actually publish
        # if self.publish_media(container_id):
        #     print("\n🎉 Instagram post published successfully!")
        # else:
        #     print("\n❌ Failed to publish Instagram post")
        
        print("\n✅ Test completed successfully!")

def main():
    """Main function to run tests"""
    print("Instagram API Testing Tool")
    print("=" * 30)
    
    # Check environment variables
    access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN')
    user_id = os.getenv('INSTAGRAM_USER_ID')
    
    if not access_token:
        print("❌ INSTAGRAM_ACCESS_TOKEN environment variable not set")
        print("Set it with: export INSTAGRAM_ACCESS_TOKEN='your_token'")
        return
    
    if not user_id:
        print("❌ INSTAGRAM_USER_ID environment variable not set")
        print("Set it with: export INSTAGRAM_USER_ID='your_user_id'")
        return
    
    # Run tests
    tester = InstagramAPITester()
    tester.run_comprehensive_test()

if __name__ == "__main__":
    main()
