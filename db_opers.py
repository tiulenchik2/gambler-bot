import psycopg2
from os import getenv
from dotenv import load_dotenv

load_dotenv()
connect = psycopg2.connect(
    dbname=getenv("DATABASE_NAME"),
    user=getenv("POSTGRESQL_USERNAME"),
    password=getenv("POSTGRESQL_PASSWORD"),
    host=getenv("SERVER_IP"),
    port=getenv("SERVER_PORT"))

cur = connect.cursor()

def add_user(username, user_id, chat_id):
    """
    Add a new user to the database.
    """
    cur.execute(
        "INSERT INTO users (username, user_id, chat_id) VALUES (%s, %s, %s) ON CONFLICT (user_id) DO NOTHING;",
        (username, user_id, chat_id)
    )
    connect.commit()

def get_user(user_id):
    """
    Get user information from the database by user_id.
    """
    cur.execute("SELECT * FROM users WHERE user_id = %s;", (user_id,))
    return cur.fetchone()

def update_score(user_id, score_delta):
    """
    Update the user's score by adding score_delta.
    """
    cur.execute("UPDATE users SET score = score + %s WHERE user_id = %s;", (score_delta, user_id))
    connect.commit()
def get_sorted_users_by_score(chat_id, limit=None):
    """
    Returns list of users from chat (chat_id), sorted by descending "score".
    If "limit" is specified, returns only that many users.
    """
    query = "SELECT * FROM users WHERE chat_id = %s ORDER BY score DESC"
    params = [chat_id]
    if limit is not None:
        query += " LIMIT %s"
        params.append(limit)
    cur.execute(query, tuple(params))
    return cur.fetchall()
def is_user_exists(user_id, chat_id):
    """
    Checks if a user exists in the database for a specific chat.
    """
    cur.execute("SELECT EXISTS(SELECT 1 FROM users WHERE user_id = %s AND chat_id = %s);", 
                (user_id, chat_id))
    return cur.fetchone()[0]

def get_users_by_chat(chat_id):
    """
    Returns all users in a specific chat.
    """
    cur.execute("SELECT * FROM users WHERE chat_id = %s;", (chat_id,))
    return cur.fetchall()

def get_user_rank(user_id, chat_id):
    """
    Returns the rank of a user in a specific chat based on their score.
    """
    cur.execute("""
        SELECT position FROM (
            SELECT user_id, ROW_NUMBER() OVER (ORDER BY score DESC) AS position 
            FROM users WHERE chat_id = %s
        ) AS ranks WHERE user_id = %s;
    """, (chat_id, user_id))
    result = cur.fetchone()
    return result[0] if result else None

def update_rolls_total(user_id, count=1):
    """
    Adds to the user's total rolls count.
    """
    cur.execute("UPDATE users SET spins = spins + %s WHERE user_id = %s;", 
                (count, user_id))
    connect.commit()

def update_rolls_win(user_id, count=1):
    """
    Adds to the user's winning rolls count.
    """
    cur.execute("UPDATE users SET wins = wins + %s WHERE user_id = %s;", 
                (count, user_id))
    connect.commit()
