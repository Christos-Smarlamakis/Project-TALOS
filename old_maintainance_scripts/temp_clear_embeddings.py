# -*- coding: utf-8 -*-
#  Project TALOS
#  Copyright (C) 2026 Christos Smarlamakis
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  For commercial licensing, please contact the author.
import sqlite3
    
print("Connecting to database...")
conn = sqlite3.connect("talos_research.db")
cursor = conn.cursor()
print("Executing UPDATE command...")
cursor.execute("UPDATE papers SET embedding = NULL")
print(f"{cursor.rowcount} rows affected.")
print("Committing changes...")
conn.commit()
print("Changes committed successfully.")
conn.close()
print("Connection closed. Process finished.")
input("Press Enter to exit.")