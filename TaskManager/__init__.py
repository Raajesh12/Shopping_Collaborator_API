import flask
from ast import literal_eval as make_tuple
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
        cur = conn.cursor()
        cur.execute('DELETE FROM users WHERE uid = %s', (uid,))
        conn.commit()
        cur.close()

        response = flask.Response(status=204)
        return response

class GroupAPI(MethodView):
    def get(self):
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
        cur = conn.cursor()
        cur.execute("DELETE FROM groups WHERE gid = %s;", (gid,))
        cur.execute("DELETE FROM group_user_match WHERE gid = %s;", (gid,))
        conn.commit()
        cur.close()
        response = flask.Response(status=204)
        return response
    
class TaskAPI(MethodView):
    # def get(self):
    #     gid = request.args.get("gid")
    #     cur = conn.cursor()
    #     cur.execute("SELECT (users.first_name, users.last_name, tasks.task_desription) FROM tasks INNER JOIN users ON users.uid = tasks.uid WHERE tasks.gid=%s;", (gid,))
    #     data = {'tasks' : []}
    #     for row in cur:
    #         row_tuple = make_tuple(row[0])
    #         row_data = {'first_name':row_tuple[0], 'last_name':row_tuple[1], 'task_description':row_tuple[2]}
    #         data['tasks'].append(row_data)
    #     cur.close()
    #     return jsonify(data), 200

    def post(self):
        """
        {
         "uid":<uid>
         "gid":<gid>
         "task_description":<task_description>
        }
        """
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
    
    # def delete(self, task_id)
    #     cur = conn.cursor()
    #     cur.execute("DELETE FROM tasks WHERE id = %s;", (task_id,))
    #     conn.commit()
    #     cur.close()
    #     response = flask.Response(status=204)
    #     return response

user_view = UserAPI.as_view('user_api')
app.add_url_rule('/users/', view_func=user_view, methods=['POST',])
app.add_url_rule('/users/<int:uid>', view_func=user_view, methods=['GET','PUT', 'DELETE'])

group_view = GroupAPI.as_view('group_api')
app.add_url_rule('/groups', view_func=group_view, methods=['GET'])
app.add_url_rule('/groups/', view_func=group_view, methods=['POST',])
app.add_url_rule('/groups/<int:gid>', view_func=group_view, methods=['PUT', 'DELETE'])

task_view = TaskAPI.as_view('task_api')
app.add_url_rule('/tasks', view_func=task_view, methods=['POST',])
# app.add_url_rule('/tasks/<int:task_id>', view_func=task_view, methods=['DELETE',])

if __name__ == "__main__":
    app.run()
