import flask
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
    def get(self, uid):
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE uid = %s;", (uid,))
        row = cur.fetchone()
        data = {
            'first_name': row[1],
            'last_name': row[2],
            'email': row[3]
        }
        return jsonify(data), 200

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
        cur.execute("INSERT INTO users (first_name, last_name, email, password, created, last_modified) VALUES (%s, %s, %s, %s, %s, %s) RETURNING uid;", (first_name, last_name, email, password, dt, dt))
        uid = cur.fetchone()
        data = {
            'uid': uid[0]
        }
        conn.commit()
        cur.close()
        return jsonify(data), 201

    def put(self, uid):
        """
        Example JSON (you need at least one of the keys)
        {
            (optional) 'first_name':<first name>,
            (optional) 'last_name':<last name>,
            (optional) 'email':<email>,
            (optional) 'password':<password>
        }
        """
        json = request.get_json()

        values_to_update = {}
        first_name = json.get('first_name')
        if first_name is not None:
            values_to_update['first_name'] = first_name

        last_name = json.get('last_name')
        if last_name is not None:
            values_to_update['last_name'] = last_name

        email = json.get('email')
        if email is not None:
            values_to_update['email'] = email

        password = json.get('password')
        if password is not None:
            values_to_update['password'] = password

        cur = conn.cursor()
        sql = 'UPDATE users SET '
        for key in values_to_update:
            update_str = key + ' = ' + '\'' + values_to_update[key] + '\'' + ', '
            sql += update_str

        substring_index = len(sql) - 2
        sql = sql[0:substring_index]
        sql += (' WHERE uid = ' + str(uid) + ';')
        cur.execute(sql)
        conn.commit()
        cur.close()

        response = flask.Response(status=204)
        return response

    def delete(self, uid):
        cur = conn.cursor()
        cur.execute('DELETE FROM users WHERE uid = %s', (uid,))
        conn.commit()
        cur.close()

        response = flask.Response(status=204)
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
app.add_url_rule('/users/<int:uid>', view_func=user_view, methods=['GET','PUT', 'DELETE'])

if __name__ == "__main__":
    app.run()

