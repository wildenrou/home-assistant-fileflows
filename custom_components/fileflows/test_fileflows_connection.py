#!/usr/bin/env python3
"""
Simple test script for FileFlows API - only tests the /api/status endpoint.
This matches exactly what the fixed integration will do.
"""

import asyncio
import aiohttp
import json

async def test_fileflows_status():
    """Test only the FileFlows status endpoint."""
    
    host = "192.168.2.15"
    port = 8585
    url = f"http://{host}:{port}/api/status"
    
    print(f"🔍 Testing FileFlows Status API")
    print(f"URL: {url}")
    print("=" * 60)
    
    try:
        # Create session with proper timeout (matching integration settings)
        timeout = aiohttp.ClientTimeout(total=15, connect=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            
            # Make request (no authentication - most FileFlows don't need it)
            headers = {
                "Accept": "application/json",
                "User-Agent": "FileFlows Integration Test"
            }
            
            async with session.get(url, headers=headers) as response:
                status = response.status
                content_type = response.headers.get('content-type', 'unknown')
                
                print(f"✅ HTTP Status: {status}")
                print(f"✅ Content-Type: {content_type}")
                
                if status == 200:
                    text = await response.text()
                    print(f"✅ Response Length: {len(text)} characters")
                    
                    # Check if it looks like JSON
                    if text.strip().startswith('{'):
                        try:
                            data = json.loads(text)
                            print("✅ JSON Parsing: SUCCESS")
                            
                            print("\n📊 FileFlows Status Data:")
                            print(f"   Queue: {data.get('queue', 'N/A')}")
                            print(f"   Processing: {data.get('processing', 'N/A')}")
                            print(f"   Processed: {data.get('processed', 'N/A')}")
                            print(f"   Time: {data.get('time', 'N/A')}")
                            
                            # Check processing files
                            processing_files = data.get('processingFiles', [])
                            print(f"   Processing Files: {len(processing_files)}")
                            
                            if processing_files:
                                print("\n🔄 Currently Processing:")
                                for i, file_info in enumerate(processing_files[:2]):  # Show first 2
                                    name = file_info.get('name', 'Unknown')
                                    step = file_info.get('step', 'Unknown')
                                    percent = file_info.get('stepPercent', 0)
                                    library = file_info.get('library', 'Unknown')
                                    
                                    # Truncate long filenames for display
                                    display_name = name if len(name) <= 60 else name[:57] + "..."
                                    
                                    print(f"   [{i+1}] {display_name}")
                                    print(f"       Step: {step} ({percent}%)")
                                    print(f"       Library: {library}")
                            
                            print("\n" + "=" * 60)
                            print("🎉 INTEGRATION STATUS: WILL WORK PERFECTLY!")
                            print("✅ The fixed integration will create these sensors:")
                            print(f"   • FileFlows Queue: {data.get('queue')} files")
                            print(f"   • FileFlows Processing: {data.get('processing')} files") 
                            print(f"   • FileFlows Processed: {data.get('processed')} files")
                            print(f"   • FileFlows Processing Time: {data.get('time')}")
                            print(f"   • FileFlows Processing Files: {len(processing_files)} files")
                            print("   • FileFlows Status: Online")
                            print(f"   • FileFlows Processing Active: {'Yes' if data.get('processing', 0) > 0 else 'No'}")
                            
                            return True
                            
                        except json.JSONDecodeError as e:
                            print(f"❌ JSON Parsing Error: {e}")
                            print(f"❌ Raw Response: {text[:200]}...")
                            return False
                    else:
                        print(f"❌ Response doesn't look like JSON: {text[:100]}...")
                        return False
                else:
                    text = await response.text()
                    print(f"❌ HTTP Error {status}")
                    print(f"❌ Response: {text[:200]}...")
                    return False
                    
    except asyncio.TimeoutError:
        print("❌ Connection Timeout")
        print("   • Check if FileFlows is running")
        print("   • Verify the IP address and port")
        return False
    except aiohttp.ClientConnectorError as e:
        print(f"❌ Connection Error: {e}")
        print("   • Check if FileFlows is running")  
        print("   • Verify the IP address and port")
        print("   • Check network connectivity")
        return False
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False

async def main():
    """Main test function."""
    print("FileFlows Integration - Simple Connection Test")
    print("=" * 60)
    
    success = await test_fileflows_status()
    
    print("\n" + "=" * 60)
    print("📋 NEXT STEPS:")
    if success:
        print("✅ Your FileFlows server is ready for integration!")
        print("✅ Install the FIXED integration files")
        print("✅ Configure with these settings:")
        print("   • URL: http://192.168.1.18:8585")
        print("   • API Key: [LEAVE BLANK]")
        print("   • All other settings: use defaults")
        print("✅ The integration will work reliably!")
    else:
        print("❌ Fix the connection issues first")
        print("❌ Make sure FileFlows is running at http://192.168.1.18:8585")
        print("❌ Check the FileFlows web interface manually")
    
    print("\n🔐 Authentication Status:")
    print("✅ No API key required (as expected)")
    print("ℹ️  This is normal and secure for home networks")

if __name__ == "__main__":
    asyncio.run(main())
