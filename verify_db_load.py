import psycopg2
conn = psycopg2.connect(host='localhost', dbname='medical', user='postgres', password='Pass@123')
cur = conn.cursor()
tables = ['patients', 'organizations', 'providers', 'payers', 'encounters', 'conditions', 'medications', 'procedures', 'observations', 'immunizations', 'allergies', 'care_plans']
for t in tables:
    try:
        cur.execute(f"SELECT count(*) FROM clinical_data.{t}")
        print(f"{t}: {cur.fetchone()[0]}")
    except Exception as e:
        print(f"{t}: Error - {e}")
        conn.rollback()
conn.close()
