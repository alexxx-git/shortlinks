import redis

r = redis.StrictRedis(host='localhost', port=6379, password='mypassword')

print(r.ping())  
