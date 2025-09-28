#!/usr/bin/env python3
"""
Test script to verify concurrent message handling works correctly.
This simulates multiple users sending messages simultaneously.
"""

import asyncio
import aiohttp
import time
from typing import List, Dict, Any

# Configuration
API_URL = "http://localhost:8000"
TEST_MESSAGES = [
    {"user_id": "5511999990001@c.us", "message": "Hello, I want to buy coffee"},
    {"user_id": "5511999990002@c.us", "message": "Hi, I need a mobile plan"},
    {"user_id": "5511999990003@c.us", "message": "Can you help me with a PIX transfer?"},
    {"user_id": "5511999990004@c.us", "message": "I want to pay a bill"},
    {"user_id": "5511999990005@c.us", "message": "Hello sofIA!"},
]

async def send_message(session: aiohttp.ClientSession, user_id: str, message: str) -> Dict[str, Any]:
    """Send a single message to the API"""
    try:
        start_time = time.time()
        
        async with session.post(
            f"{API_URL}/process-whatsapp-message",
            json={"user_id": user_id, "message": message},
            timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            end_time = time.time()
            response_data = await response.json()
            
            return {
                "user_id": user_id,
                "message": message,
                "status": response.status,
                "response": response_data,
                "duration": end_time - start_time,
                "success": response.status == 200
            }
    except Exception as e:
        return {
            "user_id": user_id,
            "message": message,
            "status": 0,
            "response": {"error": str(e)},
            "duration": 0,
            "success": False
        }

async def test_concurrent_messages():
    """Test concurrent message processing"""
    print("🧪 Testing Concurrent Message Handling")
    print("=" * 50)
    
    # Test 1: Sequential messages (baseline)
    print("\n📝 Test 1: Sequential Messages (Baseline)")
    sequential_results = []
    
    async with aiohttp.ClientSession() as session:
        for msg_data in TEST_MESSAGES[:3]:  # Test first 3 messages
            result = await send_message(session, msg_data["user_id"], msg_data["message"])
            sequential_results.append(result)
            print(f"  ✅ {msg_data['user_id'][-8:]}: {result['duration']:.2f}s - {result['success']}")
    
    # Test 2: Concurrent messages (the real test)
    print("\n🚀 Test 2: Concurrent Messages (5 simultaneous)")
    concurrent_start = time.time()
    
    async with aiohttp.ClientSession() as session:
        tasks = [
            send_message(session, msg_data["user_id"], msg_data["message"])
            for msg_data in TEST_MESSAGES
        ]
        concurrent_results = await asyncio.gather(*tasks, return_exceptions=True)
    
    concurrent_end = time.time()
    total_concurrent_time = concurrent_end - concurrent_start
    
    print(f"  ⏱️  Total concurrent time: {total_concurrent_time:.2f}s")
    
    # Analyze results
    successful_concurrent = [r for r in concurrent_results if isinstance(r, dict) and r.get('success')]
    failed_concurrent = [r for r in concurrent_results if isinstance(r, dict) and not r.get('success')]
    exceptions = [r for r in concurrent_results if isinstance(r, Exception)]
    
    print(f"  ✅ Successful: {len(successful_concurrent)}")
    print(f"  ❌ Failed: {len(failed_concurrent)}")
    print(f"  💥 Exceptions: {len(exceptions)}")
    
    # Show individual results
    for result in concurrent_results:
        if isinstance(result, dict):
            status_icon = "✅" if result['success'] else "❌"
            print(f"    {status_icon} {result['user_id'][-8:]}: {result['duration']:.2f}s - {result.get('response', {}).get('reply', 'No reply')[:50]}...")
        else:
            print(f"    💥 Exception: {result}")
    
    # Test 3: Check session stats
    print("\n📊 Test 3: Session Statistics")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_URL}/sessions") as response:
                if response.status == 200:
                    stats = await response.json()
                    print(f"  📈 Active sessions: {stats.get('active_sessions', 0)}")
                    print(f"  🔒 Active locks: {stats.get('active_locks', 0)}")
                    print(f"  👥 Session IDs: {stats.get('session_ids', [])}")
                else:
                    print(f"  ❌ Failed to get session stats: {response.status}")
    except Exception as e:
        print(f"  💥 Error getting session stats: {e}")
    
    # Summary
    print("\n📋 Summary")
    print("=" * 30)
    
    if len(successful_concurrent) == len(TEST_MESSAGES):
        print("🎉 SUCCESS: All concurrent messages processed successfully!")
        print("✅ Concurrent message handling is working correctly")
    else:
        print("⚠️  PARTIAL SUCCESS: Some messages failed")
        print("🔧 Check the error details above")
    
    if len(exceptions) > 0:
        print("💥 CRITICAL: Exceptions occurred during concurrent processing")
        print("🚨 This indicates a serious concurrency issue")
    
    # Performance comparison
    avg_sequential = sum(r['duration'] for r in sequential_results) / len(sequential_results)
    avg_concurrent = sum(r['duration'] for r in successful_concurrent) / len(successful_concurrent) if successful_concurrent else 0
    
    print(f"\n⚡ Performance:")
    print(f"  Sequential avg: {avg_sequential:.2f}s per message")
    print(f"  Concurrent avg: {avg_concurrent:.2f}s per message")
    print(f"  Total time saved: {(avg_sequential * len(TEST_MESSAGES)) - total_concurrent_time:.2f}s")

if __name__ == "__main__":
    print("🚀 Starting Concurrent Message Test")
    print("Make sure the sofIA server is running on http://localhost:8000")
    print("Press Ctrl+C to cancel")
    
    try:
        asyncio.run(test_concurrent_messages())
    except KeyboardInterrupt:
        print("\n⏹️  Test cancelled by user")
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()
