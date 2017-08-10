import flask
from ast import literal_eval as make_tuple
from flask import Flask, jsonify, request
from flask.views import MethodView
import psycopg2
import traceback
from datetime import datetime

app = Flask(__name__)

conn = psycopg2.connect(dbname="taskbase", user="www-data")

def home():
    return jsonify({'home': 'This is the homepage'}), 200

class UserAPI(MethodView):
    def get(self, uid):
        auth = request.headers.get('Authorization')
        if auth != '5c8ab94e-3c95-40f9-863d-e31ae49e5d8d':
            response = flask.Response(status=403)
            return response

        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE uid = %s;", (uid,))
        row = cur.fetchone()
        data = {
            'first_name': row[1],
            'last_name': row[2],
            'email': row[3]
        }
        cur.close()
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
        auth = str(request.headers.get('Authorization'))
        if auth != '5c8ab94e-3c95-40f9-863d-e31ae49e5d8d':
            return jsonify({'data':str(request.headers)}), 403

        json = request.get_json()
        first_name = json['first_name']
        last_name = json['last_name']
        email = json['email']
        password = json['password']
        dt = datetime.now()
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO users (first_name, last_name, email, password, created, last_modified) VALUES (%s, %s, %s, %s, %s, %s) RETURNING uid;", (first_name, last_name, email, password, dt, dt))
        except psycopg2.IntegrityError:
            data = {'error': 'email already used'}
            return jsonify(data), 400
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
        auth = request.headers.get('Authorization')
        if auth != '5c8ab94e-3c95-40f9-863d-e31ae49e5d8d':
            response = flask.Response(status=403)
            return response

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

        values_to_update['last_modified'] = str(datetime.now())

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
        auth = request.headers.get('Authorization')
        if auth != '5c8ab94e-3c95-40f9-863d-e31ae49e5d8d':
            response = flask.Response(status=403)
            return response

        cur = conn.cursor()
        cur.execute('DELETE FROM users WHERE uid = %s', (uid,))
        conn.commit()
        cur.close()

        response = flask.Response(status=204)
        return response

class GroupAPI(MethodView):
    def get(self):
        auth = request.headers.get('Authorization')
        if auth != '5c8ab94e-3c95-40f9-863d-e31ae49e5d8d':
            response = flask.Response(status=403)
            return response

        uid = request.args.get("uid")
        cur = conn.cursor()
        cur.execute("SELECT (group_user_match.gid, groups.group_name) FROM group_user_match INNER JOIN groups ON group_user_match.gid = groups.gid WHERE group_user_match.uid=%s", (uid,))
        data = {'groups' : []}
        for row in cur:
            row_tuple = make_tuple(row[0])
            row_data = {'gid':row_tuple[0], 'group_name':row_tuple[1]}
            data['groups'].append(row_data)
        cur.close()
        return jsonify(data), 200

    def post(self):
        """
        {
            "uid": <uid>
            "group_name": <group_name>
        }
        
        """
        auth = request.headers.get('Authorization')
        if auth != '5c8ab94e-3c95-40f9-863d-e31ae49e5d8d':
            response = flask.Response(status=403)
            return response

        cur = conn.cursor()
        json = request.get_json()
        group_name = json["group_name"]
        uid = json["uid"]
        date = datetime.now()
        cur.execute("INSERT INTO groups (group_name, created, last_modified) VALUES (%s, %s, %s) RETURNING gid;", (group_name, date, date))
        gid = cur.fetchone()[0]
        cur.execute("INSERT INTO group_user_match (gid, uid, created, last_modified) VALUES (%s, %s, %s, %s);", (gid, uid, date, date))
        conn.commit()
        cur.close()
        return jsonify({"gid": gid}), 201
    
    def put(self, gid):
        '''
        {
            "group_name":<group_name>
        }
        '''
        auth = request.headers.get('Authorization')
        if auth != '5c8ab94e-3c95-40f9-863d-e31ae49e5d8d':
            response = flask.Response(status=403)
            return response

        cur = conn.cursor()
        json = request.get_json()
        group_name = json["group_name"]
        date = datetime.now()
        cur.execute("UPDATE groups SET group_name = %s, last_modified = %s WHERE gid = %s;", (group_name, date, gid))
        conn.commit()
        cur.close()
        response = flask.Response(status=204)
        return response

    def delete(self, gid):
        auth = request.headers.get('Authorization')
        if auth != '5c8ab94e-3c95-40f9-863d-e31ae49e5d8d':
            response = flask.Response(status=403)
            return response

        cur = conn.cursor()
        cur.execute("DELETE FROM groups WHERE gid = %s;", (gid,))
        cur.execute("DELETE FROM group_user_match WHERE gid = %s;", (gid,))
        conn.commit()
        cur.close()
        response = flask.Response(status=204)
        return response
    
class TaskAPI(MethodView):
    def get(self):
        auth = request.headers.get('Authorization')
        if auth != '5c8ab94e-3c95-40f9-863d-e31ae49e5d8d':
            response = flask.Response(status=403)
            return response

        gid = request.args.get("gid")
        cur = conn.cursor()
        cur.execute("SELECT (users.first_name, users.last_name, tasks.task_description) FROM tasks INNER JOIN users ON users.uid = tasks.uid WHERE tasks.gid=%s;", (gid,))
        data = {'tasks' : []}
        for row in cur:
            components = row[0].split(',')
            for i in range(0, len(components)):
                components[i] = components[i].replace('(', '')
                components[i] = components[i].replace('\"', '')
                components[i] = components[i].replace(')', '')
            row_data = {'first_name':components[0], 'last_name':components[1], 'task_description':components[2]}
            data['tasks'].append(row_data)
        cur.close()
        return jsonify(data), 200

    def post(self):
        """
        {
         "uid":<uid>
         "gid":<gid>
         "task_description":<task_description>
        }
        """
        auth = request.headers.get('Authorization')
        if auth != '5c8ab94e-3c95-40f9-863d-e31ae49e5d8d':
            response = flask.Response(status=403)
            return response

        cur = conn.cursor()
        json = request.get_json()
        uid = json["uid"]
        gid = json["gid"]
        task_description = json["task_description"]
        date = datetime.now()
        cur.execute("INSERT INTO tasks (gid, uid, task_description, created, last_modified) VALUES (%s, %s, %s, %s, %s) RETURNING id;", (gid, uid, task_description, date, date))
        task_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        return jsonify({"id": task_id}), 201
    
    def put(self, task_id):
        """
        {
        "task_description": <task_description>
        }
        """
        auth = request.headers.get('Authorization')
        if auth != '5c8ab94e-3c95-40f9-863d-e31ae49e5d8d':
            response = flask.Response(status=403)
            return response

        cur = conn.cursor()
        json = request.get_json()
        task_description = json["task_description"]
        dt = datetime.now()
        cur.execute("UPDATE tasks SET task_description = %s, last_modified = %s WHERE id = %s;", (task_description, dt, task_id))
        conn.commit()
        cur.close()
        response = flask.Response(status=204)
        return response

    def delete(self, task_id):
        auth = request.headers.get('Authorization')
        if auth != '5c8ab94e-3c95-40f9-863d-e31ae49e5d8d':
            response = flask.Response(status=403)
            return response

        cur = conn.cursor()
        cur.execute("DELETE FROM tasks WHERE id=%s", (task_id,))
        conn.commit()
        cur.close()
        response = flask.Response(status=204)
        return response
    
class GroupUserAPI(MethodView):
    def post(self):
        """
        {
        "gid":<gid>
        "user_email":<user_email>
        }
        """
        auth = request.headers.get('Authorization')
        if auth != '5c8ab94e-3c95-40f9-863d-e31ae49e5d8d':
            response = flask.Response(status=403)
            return response

        cur = conn.cursor()
        json = request.get_json()
        gid = json["gid"]
        user_email = json["user_email"]
        dt = datetime.now()
        cur.execute("SELECT (uid) FROM users WHERE email = %s;", (user_email,))
        uid = cur.fetchone()[0]
        if(uid is None):
            return jsonify({"error": "user not found"}), 400
        cur.execute("INSERT INTO group_user_match (gid, uid, created, last_modified) VALUES (%s, %s, %s, %s);", (gid, uid, dt, dt))
        conn.commit()
        cur.close()
        response = flask.Response(status=201)
        return response

    def delete(self):
        auth = request.headers.get('Authorization')
        if auth != '5c8ab94e-3c95-40f9-863d-e31ae49e5d8d':
            response = flask.Response(status=403)
            return response

        cur = conn.cursor()
        gid = request.args.get("gid")
        uid = request.args.get("uid")
        cur.execute("DELETE FROM group_user_match WHERE gid = %s AND uid = %s;", (gid, uid))
        conn.commit()
        cur.close()
        response = flask.Response(status=204)
        return response

def validate_user():
    """
    JSON format
    {
        'email':<email>
        'password':<password>
    }
    """
    auth = request.headers.get('Authorization')
    if auth != '5c8ab94e-3c95-40f9-863d-e31ae49e5d8d':
        response = flask.Response(status=403)
        return response

    json = request.get_json()
    email = json['email']
    password = json['password']
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email = %s AND password = %s;", (email, password))
    row = cur.fetchone()
    if row is None:
        response = flask.Response(status=401)
        return response
    response = flask.Response(status=200)
    return response

app.add_url_rule('/', 'home', home, methods=['GET'])
app.add_url_rule('/validate_user', 'validate_user', validate_user, methods=['POST'])

user_view = UserAPI.as_view('user_api')
app.add_url_rule('/users/', view_func=user_view, methods=['POST',])
app.add_url_rule('/users/<int:uid>', view_func=user_view, methods=['GET','PUT', 'DELETE'])

group_view = GroupAPI.as_view('group_api')
app.add_url_rule('/groups', view_func=group_view, methods=['GET'])
app.add_url_rule('/groups/', view_func=group_view, methods=['POST',])
app.add_url_rule('/groups/<int:gid>', view_func=group_view, methods=['PUT', 'DELETE'])

task_view = TaskAPI.as_view('task_api')
app.add_url_rule('/tasks', view_func=task_view, methods=['POST', 'GET'])
app.add_url_rule('/tasks/<int:task_id>', view_func=task_view, methods=['PUT', 'DELETE'])

group_user_view = GroupUserAPI.as_view('group_user_api')
app.add_url_rule('/group_user', view_func=group_user_view, methods=['POST', 'DELETE'])

if __name__ == "__main__":
    app.run()
