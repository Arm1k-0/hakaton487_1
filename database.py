import sqlite3

class Database:
    def __init__(self, db_name='neighbor_bot.db'):
        self.db_name = db_name
        self.init_database()

    def init_database(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                phone TEXT,
                latitude REAL,
                longitude REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS help_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                category TEXT,
                description TEXT,
                details TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS help_offers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                category TEXT,
                description TEXT,
                details TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS connections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id INTEGER,
                offer_id INTEGER,
                status TEXT DEFAULT 'pending',
                chat_started BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (request_id) REFERENCES help_requests (id),
                FOREIGN KEY (offer_id) REFERENCES help_offers (id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                connection_id INTEGER,
                from_user_id INTEGER,
                message_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (connection_id) REFERENCES connections (id)
            )
        ''')

        conn.commit()
        conn.close()

    def add_user(self, user_id, username, first_name, last_name, phone=None):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, phone) VALUES (?, ?, ?, ?, ?)',
                      (user_id, username, first_name, last_name, phone))
        conn.commit()
        conn.close()

    def update_user_location(self, user_id, latitude, longitude):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET latitude = ?, longitude = ? WHERE user_id = ?', (latitude, longitude, user_id))
        conn.commit()
        conn.close()

    def create_help_request(self, user_id, category, description, details=""):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO help_requests (user_id, category, description, details) VALUES (?, ?, ?, ?)',
                      (user_id, category, description, details))
        request_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return request_id

    def create_help_offer(self, user_id, category, description, details=""):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO help_offers (user_id, category, description, details) VALUES (?, ?, ?, ?)',
                      (user_id, category, description, details))
        offer_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return offer_id

    def find_matches(self, user_id, category=None):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        if category:
            cursor.execute('''
                SELECT ho.id, ho.description, ho.details, u.first_name
                FROM help_offers ho
                JOIN users u ON ho.user_id = u.user_id
                WHERE ho.status = 'active' AND ho.category = ?
            ''', (category,))
        else:
            cursor.execute('''
                SELECT ho.id, ho.description, ho.details, u.first_name
                FROM help_offers ho
                JOIN users u ON ho.user_id = u.user_id
                WHERE ho.status = 'active'
            ''')

        volunteers = cursor.fetchall()
        conn.close()

        return [{
            'id': vol[0],
            'description': vol[1],
            'details': vol[2],
            'first_name': vol[3]
        } for vol in volunteers]

    def find_help_requests_nearby(self, user_id, category=None):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        if category:
            cursor.execute('''
                SELECT hr.id, hr.description, hr.details, u.first_name
                FROM help_requests hr
                JOIN users u ON hr.user_id = u.user_id
                WHERE hr.status = 'active' AND hr.category = ?
            ''', (category,))
        else:
            cursor.execute('''
                SELECT hr.id, hr.description, hr.details, u.first_name
                FROM help_requests hr
                JOIN users u ON hr.user_id = u.user_id
                WHERE hr.status = 'active'
            ''')

        requests = cursor.fetchall()
        conn.close()

        return [{
            'id': req[0],
            'description': req[1],
            'details': req[2],
            'first_name': req[3]
        } for req in requests]

    def get_user_requests(self, user_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT id, description, details, status FROM help_requests WHERE user_id = ?', (user_id,))
        requests = cursor.fetchall()
        conn.close()
        return [{'id': r[0], 'description': r[1], 'details': r[2], 'status': r[3]} for r in requests]

    def get_user_offers(self, user_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT id, description, details, status FROM help_offers WHERE user_id = ?', (user_id,))
        offers = cursor.fetchall()
        conn.close()
        return [{'id': o[0], 'description': o[1], 'details': o[2], 'status': o[3]} for o in offers]