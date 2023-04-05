import psycopg2
from config import config
import requests
import random

def generate_random_sentence():
    words = ["apple", "banana", "cat", "dog", "elephant", "frog", "giraffe", "horse", "iguana", "jellyfish", "kangaroo", "lion", "monkey", "noodle", "octopus", "penguin", "quail", "rabbit", "snake", "turtle", "unicorn", "vulture", "whale", "xylophone", "yak", "zebra", "worm"]
    sentence = " ".join(random.sample(words, 3))
    return sentence.capitalize()

def generate_random_difficulty():
    return random.randint(1, 5)



conn = None
try:
    # read connection parameters
    params = config()
    # connect to the PostgreSQL server
    print('Connecting to the PostgreSQL database...')
    conn = psycopg2.connect(**params)	
    # create a cursor
    cur = conn.cursor()
 
    # Add 20 users to "users" table.
    for i in range(20):
       # get the data from the API
       url = 'https://randomuser.me/api/'
       response = requests.get(url)
       if response.status_code == 200:
          people = response.json()['results'][0]
          # \" preserves the uppercase letters and required.
          cur.execute('INSERT INTO users(name, email, password) VALUES(%s, %s, %s)', (people['name']['first'] + " " + people['name']['last'], people['email'], people["login"]["md5"]))
          print("executed once")
 
    
    # Populate "tasks" table
    for i in range(200):
        cur.execute('INSERT INTO tasks(name, difficulty) VALUES(%s, %s);', (generate_random_sentence(), str(generate_random_difficulty())))
 
    # execute a statement
    # cur.execute('SELECT * FROM users')
    # results = cur.fetchall()
 
    # for row in results:
    #    print(row)
 
    conn.commit()
    cur.close()
except (Exception, psycopg2.DatabaseError) as error:
    print(error)
finally:
    if conn is not None:
        conn.close()
        print('Database connection closed.')
