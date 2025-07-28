#!/usr/bin/env python3
"""
Test script to verify FileFlows connection before updating the integration.
This uses the same API client code that will be used in the integration.
"""

import asyncio
import aiohttp
import json

async def test_fileflows_api():
    """Test the FileFlows API connection."""
    
    host = "192.168.1.18"
    port = 8585
    url = f"http://{host}:{port}/api/status"
    
    print(f"Testing FileFlows API at {url}")
    print("=" * 50)
    
    try:
        # Create session with proper timeout
        timeout = aiohttp.ClientTimeout(total=10, connect=5)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            
            # Make request with proper headers
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "FileFlows Test Script"
            }
            
            async with session.get(url, headers=headers) as response:
                print(f"✅ HTTP Status: {response.status}")
                print(f"✅ Content-Type: {response.headers.get('content-type', 'unknown')}")
                
                # Get response text
                text = await response.text()
                print(f"✅ Response Length: {len(text)} characters")
                
                if response.status == 200:
                    try:
                        # Parse JSON
                        data = json.loads(text)
                        print("✅ JSON Parsing: SUCCESS")
                        print("\n📊 FileFlows Status Data:")
                        print(f"   Queue: {data.get('queue', 'N/A')}")
                        print(f"   Processing: {data.get('processing', 'N/A')}")
                        print(f"   Processed: {data.get('processed', 'N/A')}")
                        print(f"   Time: {data.get('time', 'N/A')}")
                        
                        processing_files = data.get('processingFiles', [])
                        print(f"   Processing Files: {len(processing_files)}")
                        
                        if processing_files:
                            print("\n🔄 Currently Processing:")
                            for i, file_info in enumerate(processing_files[:3]):  # Show first 3
                                name = file_info.get('name', 'Unknown')
                                step = file_info.get('step', 'Unknown')
                                percent = file_info.get('stepPercent', 0)
                                library = file_info.get('library', 'Unknown')
                                
                                print(f"   [{i+1}] {name}")
                                print(f"       Step: {step} ({percent}%)")
                                print(f"       Library: {library}")
                        
                        print("\n✅ API Test: PASSED")
                        print("The integration should work with your FileFlows server!")
                        
                        return True
                        
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON Parsing Error: {e}")
                        print(f"❌ Raw Response: {text[:200]}...")
                        return False
                else:
                    print(f"❌ HTTP Error {response.status}")
                    print(f"❌ Response: {text[:200]}...")
                    return False
                    
    except asyncio.TimeoutError:
        print("❌ Connection Timeout")
        print("Check if FileFlows is running and accessible")
        return False
    except aiohttp.ClientError as e:
        print(f"❌ Connection Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False

async def main():
    """Main test function."""
    print("FileFlows API Connection Test")
    print("=" * 50)
    
    success = await test_fileflows_api()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Test Result: SUCCESS")
        print("✅ Your FileFlows server is compatible!")
        print("✅ You can now apply the integration updates.")
    else:
        print("❌ Test Result: FAILED")
        print("❌ There may be connection issues.")
        print("❌ Check your FileFlows server configuration.")

if __name__ == "__main__":
    asyncio.run(main())
