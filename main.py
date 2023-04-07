import psycopg2
from config import config
import requests
import random
import csv
from datetime import datetime, timedelta

# for task name
def generate_random_sentence():
    words = ["apple", "banana", "cat", "dog", "elephant", "frog", "giraffe", "horse", "iguana", "jellyfish", "kangaroo", "lion", "monkey", "noodle", "octopus", "penguin", "quail", "rabbit", "snake", "turtle", "unicorn", "vulture", "whale", "xylophone", "yak", "zebra", "worm"]
    sentence = " ".join(random.sample(words, 3))
    return sentence.capitalize()

# for task difficulty
def generate_random_difficulty():
    return random.randint(1, 5)

def generate_random_level():
    return random.randint(1, 10)

LEVEL_WEIGHT = 0.4
DIFFICULTY_WEIGHT = 0.6


def calculate_hours(level, difficulty):
   
    # level's weight is %25
    level_factor = (11 - level) / 10 * 0.25
    # difficulty's weight is %75
    diff_factor = (6 - difficulty) / 5 * 0.75

    

    # total factor
    total_factor = level_factor + diff_factor
    # calculate the result
    result = rand_num * total_factor
    result = round(result) + 1
    return result

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
    for i in range(200):
        cur.execute('SELECT * FROM users ORDER BY RANDOM() LIMIT 1;')
        user = cur.fetchone()
        cur.execute('INSERT INTO tasks(name, difficulty, \"assigneeId\") VALUES(%s, %s, %s);', (generate_random_sentence(), generate_random_difficulty(), user[0]))
    

    # Populate "completed_tasks" table
    for i in range(200):
        cur.execute('SELECT * FROM tasks WHERE status != \'done\' ORDER BY RANDOM() LIMIT 1;')
        task = cur.fetchone()
        if(task == None):
            break
        
        with open('./data/task_data.csv', 'r') as file:
        # Create a csv reader object
            reader = csv.reader(file)

            # Get a random row from the csv file
            rows = list(reader)
            total_rows = len(rows)
            random_index = random.randint(1, total_rows - 2)
            random_row = rows[random_index]

            # started date
            date_format = '%Y-%m-%dT%H:%M:%S.%f%z'
            date1 = datetime.strptime(random_row[2], date_format)

            cur.execute('SELECT level FROM users WHERE id=%s;', (task[3],))
            user = cur.fetchone()
            level = user[0]
            # TODO - add the level of the user to the task difficulty
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
