import redis

try:
    r = redis.Redis(host='localhost', port=6379, password='As836sjdg26HTTg277')
    r.set('test_key', 'It works!')
    value = r.get('test_key')
    print(f"Retrieved value: {value.decode('utf-8')}")
    print("Redis connection successful!")
except redis.exceptions.AuthenticationError:
    print("Authentication failed. Please check your Redis password.")
except redis.exceptions.ConnectionError:
    print("Connection refused. Please check if Redis is running.")
except Exception as e:
    print(f"An error occurred: {str(e)}")