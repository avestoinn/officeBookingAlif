import database
import models

if __name__ == '__main__':
    db = database.Database()
    database.initial_records(db)

    tables = database.TablesFacade(db)
    tables.rooms.get_all()
    tables.appointments.get_all()
