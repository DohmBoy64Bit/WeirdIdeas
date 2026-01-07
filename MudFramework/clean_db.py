import sqlite3

# Connect to the database
conn = sqlite3.connect('mud.db')
cursor = conn.cursor()

# Delete all users and players
cursor.execute('DELETE FROM players')
cursor.execute('DELETE FROM users')

conn.commit()

# Get counts
cursor.execute('SELECT COUNT(*) FROM users')
user_count = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(*) FROM players')
player_count = cursor.fetchone()[0]

conn.close()

print(f"✅ Database cleaned!")
print(f"   Users: {user_count}")
print(f"   Players: {player_count}")
