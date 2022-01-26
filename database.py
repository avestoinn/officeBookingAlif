"""
В связи с тем, что движок Sqlite не обладает типами полей для хранения даты и времени, мы будем хранить их
"""
import datetime
import enum
import sqlite3

from pydantic.dataclasses import dataclass

import config
import models


class CursorWrapper(sqlite3.Cursor):
    def __init__(self, conn: sqlite3.Connection):
        super().__init__(conn)


class Database:
    _is_open: bool
    _path: str
    _conn: sqlite3.Connection
    _cursor: sqlite3.Cursor

    def __init__(self, path: str = None):
        self._path = path if path else config.Database.DB_NAME

        # Establishing a database connection
        self._conn = sqlite3.connect(self._path)
        self._create_tables()

        if path == ":memory:":
            initial_records(self)

    def get_one(self, query: str):
        with self as db:
            db.execute(query)
            res = db.fetchone()
        return res

    def get_many(self, query: str):
        with self as db:
            db.execute(query)
            res = db.fetchall()
        return res

    def _create_tables(self):
        # db = self._conn.cursor()
        with self as db:
            db.execute("PRAGMA foreign_keys=on")
            q = f"CREATE TABLE IF NOT EXISTS {RoomsTable.name} " \
                f"(id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, " \
                f"name TEXT NOT NULL)"
            db.execute(q)
            db.execute(
                f"CREATE TABLE IF NOT EXISTS {AppointmentsTable.name}"
                f"(id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,"
                f"begin_dt TEXT NOT NULL,"
                f"end_dt TEXT NOT NULL,"
                f"room_id INTEGER NOT NULL , FOREIGN KEY (room_id) REFERENCES rooms(id))"
            )
            self._conn.commit()

    def __enter__(self):
        self._is_open = False
        self._cursor = self._conn.cursor()
        return self._cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._conn.commit()
        self._cursor.close()
        self._is_open = True


def initial_records(database: Database):
    """Makes initial records to the given database"""
    try:
        with database as db:
            for i in range(1, 6):
                name = f"Офис №{i}"
                db.execute(
                    f"INSERT INTO {RoomsTable.name} (id, name) VALUES ({i}, '{name}')"
                )
    except (sqlite3.IntegrityError, sqlite3.OperationalError):
        return


class Table:
    _name: str
    _database: Database

    def __init__(self, database: Database):
        self._database = database


class RoomsTable(Table):
    _database: Database
    name = "rooms"

    def get_all(self):
        records = self._database.get_many(f"SELECT * FROM {self.name}")
        return [models.Room(id=rec[0], name=rec[1]) for rec in records]

    def get_appointments_by_room(self, room: models.Room, active_only: bool = False):
        records = self._database.get_many(f"SELECT * FROM {AppointmentsTable.name} WHERE room_id = {room.id}")
        appointments = [models.Appointment(id=r[0], begin_dt=r[1], end_dt=r[2], room_id=r[3]) for r in records]

        if active_only:
            return list(filter(lambda app: datetime.datetime.now() > app.end_dt, appointments))

        return appointments


class AppointmentsTable(Table):
    name = "appointments"

    def get_all(self):
        """Returns all the appointments from the database"""
        records = self._database.get_many(f"SELECT * FROM {self.name}")
        return [models.Appointment(id=r[0], begin_dt=r[1], end_dt=r[2], room_id=r[3]) for r in records]

    def get_active_only(self):
        """Returns only active (!) appointments"""
        records = self._database.get_many(f"SELECT * FROM {self.name}")
        res = [models.Appointment(id=r[0], begin_dt=r[1], end_dt=r[2], room_id=r[3]) for r in records]
        return list(filter(lambda app: datetime.datetime.now() > app.end_dt, res))


class TablesFacade:
    """Facade-class for one-point access to all the app's tables"""
    rooms: RoomsTable
    appointments: AppointmentsTable

    def __init__(self, database: Database):
        self.rooms = RoomsTable(database)
        self.appointments = AppointmentsTable(database)