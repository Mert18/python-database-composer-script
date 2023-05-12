import psycopg2
from config import config
import requests
import random
from datetime import datetime, timedelta
import math

# for task name
def generate_random_sentence():
    words = ["apple", "banana", "cat", "dog", "elephant", "frog", "giraffe", "horse", "iguana", "jellyfish", "kangaroo", "lion", "monkey", "noodle", "octopus", "penguin", "quail", "rabbit", "snake", "turtle", "unicorn", "vulture", "whale", "xylophone", "yak", "zebra", "worm"]
    sentence = " ".join(random.sample(words, 3))
    return sentence.capitalize()

# for task difficulty
def generate_random_difficulty():
    return random.randint(1, 10)

def generate_random_level():
    return random.randint(1, 10)

def calculate_hours(level, difficulty):
    difficultyFactor = round(math.sqrt(difficulty*difficulty*difficulty))
    levelFactor = 32 - round(math.sqrt(level*level*level))  
    average = round((difficultyFactor + levelFactor) / 2)
    randomFactor = random.randint(-3, 3)
    return average + randomFactor + 3

# connection for database
conn = None
try:
    # read database connection parameters
    params = config()
    # connect to the PostgreSQL server
    print('Connecting to the PostgreSQL database...')
    conn = psycopg2.connect(**params)	
    # create a cursor to execute commands
    cur = conn.cursor()
 
    # Add 20 users to "users" table.
    for i in range(20):
       # get the data from the API
       url = 'https://randomuser.me/api/'
       response = requests.get(url)
       level = generate_random_level()
       if response.status_code == 200:
          people = response.json()['results'][0]
          # \" preserves the uppercase letters and required.
          cur.execute('INSERT INTO users(name, email, password, level) VALUES(%s, %s, %s, %s)', (people['name']['first'] + " " + people['name']['last'], people['email'], people["login"]["md5"], level))
 
    # Populate "tasks" table with random names and difficulty, and assigneeId from "users" table.
    for i in range(1000):
        cur.execute('SELECT * FROM users ORDER BY RANDOM() LIMIT 1;')
        user = cur.fetchone()
        cur.execute('INSERT INTO tasks(name, difficulty, \"assigneeId\") VALUES(%s, %s, %s);', (generate_random_sentence(), generate_random_difficulty(), user[0]))
    

    # Populate "completed_tasks" table
    for i in range(1000):
        cur.execute('SELECT * FROM tasks WHERE status != \'done\' ORDER BY RANDOM() LIMIT 1;')
        task = cur.fetchone()
        if(task == None):
            break
        
        # started date
        date_format = '%Y-%m-%dT%H:%M:%S.%f%z'
        
        date1 = datetime.now()
        cur.execute('SELECT level FROM users WHERE id=%s;', (task[3],))
        user = cur.fetchone()
        level = user[0]

        # Generate a random number of hours to complete the task: SENSIVITY OF THE DATA to generate the completed_date
        difficulty = task[10]
        hours_to_complete = calculate_hours(level, difficulty)
        completed_date = date1 + timedelta(hours=hours_to_complete)

        # get the difference in hours - how many hours did it take?
        delta = completed_date - date1
        hours = delta.total_seconds() // 3600

        # insert into completed_tasks 
        cur.execute('INSERT INTO completed_tasks(task_id, user_id, started_date, completed_date, user_level, task_difficulty, hours) VALUES(%s, %s, %s, %s, %s, %s, %s);', (task[0], task[3], date1, completed_date, level, difficulty, hours))

        # update the task status to done
        cur.execute('UPDATE tasks SET status = \'done\' WHERE id = %s;', (task[0],))

    # commit the changes to the database
    conn.commit()
    # close the communication with the PostgreSQL
    cur.close()
except (Exception, psycopg2.DatabaseError) as error:
    print(error)
finally:
    if conn is not None:
        conn.close()
        print('Database connection closed.')
