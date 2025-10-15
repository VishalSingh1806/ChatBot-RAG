import redis
import os
from dotenv import load_dotenv

load_dotenv()

# Connect to Redis
redis_client = redis.StrictRedis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=0,
    decode_responses=True
)

# Test session ID
test_session = "test_session_123"
chat_key = f"session:{test_session}:chat"

# Clear any existing test data
redis_client.delete(chat_key)

# Add test messages
print("Adding test messages...")
redis_client.rpush(chat_key, "User: What is EPR?")
redis_client.rpush(chat_key, "Bot: EPR stands for Extended Producer Responsibility...")
redis_client.rpush(chat_key, "User: How to register?")
redis_client.rpush(chat_key, "Bot: To register for EPR, you need...")

# Check what was saved
print(f"\nChecking Redis key: {chat_key}")
print(f"Key exists: {redis_client.exists(chat_key)}")
print(f"Total messages: {redis_client.llen(chat_key)}")

# Retrieve all messages
messages = redis_client.lrange(chat_key, 0, -1)
print(f"\nRetrieved {len(messages)} messages:")
for i, msg in enumerate(messages, 1):
    print(f"{i}. {msg}")

# Clean up
redis_client.delete(chat_key)
print("\nTest completed!")
