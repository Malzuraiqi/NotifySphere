import sqlite3

class Database:
    def insert_tasks(self, details):
        try:
            connection = sqlite3.connect("tasks.db")
            cursor = connection.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY,
                    day INTEGER,
                    course TEXT,
                    assignment TEXT,
                    status TEXT,
                    due_date TEXT,
                    url TEXT,
                    UNIQUE(course, assignment)
                )
            ''')

            for task in details:
                # UNIQUE(course, assignment) is the condition for IGNORE
                cursor.execute('''
                        INSERT OR IGNORE INTO tasks (day, course, assignment, status, due_date, url)
                        VALUES (:day, :course, :assignment, :status, :due_date, :url)
                    ''', task)
            
            inserted_count = cursor.rowcount
            print(inserted_count)

            connection.commit()

        except sqlite3.Error as e:
            print(f"Database Error: {e}")
            connection.rollback()
        
        finally:
            if connection:
                connection.close()

    def get_tasks_details(self):
        try:
            connection = sqlite3.connect("tasks.db")
            cursor = connection.cursor()

            cursor.execute("SELECT day, course, assignment, status, due_date, url FROM tasks ORDER BY day ASC")

            columns = [description[0] for description in cursor.description]

            all_days = []
            for row in cursor:
                task_dict = dict(zip(columns, row))
                all_days.append(task_dict)

            return all_days

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []

        finally:
            if connection:
                connection.close()

    def get_tasks_for_comparison(self):
        try:
            connection = sqlite3.connect("tasks.db")
            cursor = connection.cursor()

            cursor.execute("SELECT day, assignment FROM tasks WHERE status='Submitted for grading'")

            all_days = []
            for row in cursor:
                day_tuple = (int(row[0]), row[1])
                all_days.append(day_tuple)

            return all_days

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []

        finally:
            if connection:
                connection.close()