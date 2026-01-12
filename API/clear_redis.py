import redis

# Connect to Redis
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# Clear all data
redis_client.flushdb()

print("✅ Redis database cleared successfully!")
