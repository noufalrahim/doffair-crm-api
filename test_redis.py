"""
Quick test to check if Redis is running
Run: python test_redis.py
"""
import redis

try:
    # Connect to Redis (use 127.0.0.1 for Windows/Docker compatibility)
    r = redis.Redis(host='127.0.0.1', port=6379, decode_responses=True, socket_connect_timeout=5)
    
    # Test connection
    response = r.ping()
    
    if response:
        print("✅ SUCCESS! Redis is running and accepting connections")
        print(f"   Host: 127.0.0.1")
        print(f"   Port: 6379")
        
        # Test basic operations
        r.set('test_key', 'Hello from Doffair!')
        value = r.get('test_key')
        print(f"   Test write/read: {value}")
        
        # Clean up
        r.delete('test_key')
        print("\n🎉 Redis is ready for the notification engine!")
    else:
        print("❌ Redis responded but something is wrong")
        
except redis.ConnectionError:
    print("❌ ERROR: Cannot connect to Redis")
    print("\nTroubleshooting:")
    print("1. Check if Redis server is running")
    print("2. Verify Redis is running on localhost:6379")
    print("3. Check firewall settings")
    print("\nIf you installed Memurai:")
    print("   - Check Windows Services (Win+R → services.msc)")
    print("   - Look for 'Memurai' service")
    print("   - Make sure it's running")
    
except Exception as e:
    print(f"❌ ERROR: {str(e)}")
