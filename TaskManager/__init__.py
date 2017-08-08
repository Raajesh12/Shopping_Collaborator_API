from flask import Flask, jsonify, request
from flask.views import MethodView
import psycopg2
import traceback
from datetime import datetime

app = Flask(__name__)

conn = psycopg2.connect(dbname="taskbase", user="www-data")

@app.route("/", methods=['GET'])
def home():
    return jsonify({'home': 'This is the homepage'}), 200

class UserAPI(MethodView):
    def post(self):
        """
        Example JSON for this request
        {
            'first_name':<first name>,
            'last_name':<last_name>,
            'email':<email>,
            'password':<email>
        }
        """
        json = request.get_json()
        first_name = json['first_name']
        last_name = json['last_name']
        email = json['email']
        password = json['password']
        dt = datetime.now()
        cur = conn.cursor()
        cur.execute("INSERT INTO users (first_name, last_name, email, password, created, last_modified) VALUES (%s, %s, %s, %s, %s, %s);", (first_name, last_name, email, password, dt, dt))
        conn.commit()
        cur.close()
        response = make_response()
        response.status = 201
        return response

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

user_view = UserAPI.as_view('user_api')
app.add_url_rule('/users/', view_func=user_view, methods=['POST',])

if __name__ == "__main__":
    app.run()

