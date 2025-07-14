import sqlite3

def getDbConnection(withRow=True):
    # Open database connection and return cursor, option to return indexed and named access to columns
    con = sqlite3.connect('outfits.db')
    if withRow:
        con.row_factory = sqlite3.Row

    return con

def dbInsert(query, values):
    db = getDbConnection(False)
    cur = db.cursor()
    cur.execute(query, values)
    rowId = cur.lastrowid
    db.commit()
    db.close()

    return rowId

def dbSelect(query, values=None):
    db = getDbConnection(True)
    cur = db.cursor()
    if values:
        data = cur.execute(query, values).fetchall()
    else:
        data = cur.execute(query).fetchall()
    db.close()
    
    return data