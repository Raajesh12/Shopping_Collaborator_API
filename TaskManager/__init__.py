from flask import Flask, jsonify
import psycopg2
import traceback

app = Flask(__name__)

@app.route("/", methods=['GET'])
def home():
    return jsonify({'home': 'This is the homepage'}), 200

@app.route("/add_task", methods=['POST'])
def create_test():
    conn = psycopg2.connect(dbname="ourbase", user="www-data")
    cur = conn.cursor()
    cur.execute("CREATE TABLE test (id serial PRIMARY KEY, num integer, data varchar);")
    cur.execute("INSERT INTO test (num, data) VALUES (%s, %s)", (100, "abc'def"))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'data':'data'}), 201

@app.route("/get_task", methods=['GET'])
def get_test():
    conn = psycopg2.connect(dbname="ourbase", user="www-data")
    cur = conn.cursor()
    cur.execute("SELECT * FROM test;")
    row = cur.fetchone()
    data = {
        'id': row[0],
        'num': row[1],
        'data': row[2]
    }
    cur.close()
    conn.close()
    return jsonify({'data': data}), 200

if __name__ == "__main__":
    app.run()

