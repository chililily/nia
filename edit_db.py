import sqlite3

db = sqlite3.connect('nia_data')
c = db.cursor()

# c.execute("ALTER TABLE member_stats ADD uid TEXT;")
# c.execute("UPDATE member_stats SET uid = c_id;")
# c.execute("ALTER TABLE server_configs ADD sid INT;")
c.execute("DROP TABLE guild_configs;")
db.commit()
db.close()