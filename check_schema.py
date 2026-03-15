import psycopg2
conn = psycopg2.connect(host='localhost', dbname='medical', user='postgres', password='Pass@123')
cur = conn.cursor()
cur.execute("SELECT column_name, character_maximum_length FROM information_schema.columns WHERE table_schema='clinical_data' AND table_name='organizations' AND column_name='phone'")
print('organizations.phone length:', cur.fetchall())
cur.execute("SELECT column_name, character_maximum_length FROM information_schema.columns WHERE table_schema='clinical_data' AND table_name='payers' AND column_name='phone'")
print('payers.phone length:', cur.fetchall())
conn.close()
