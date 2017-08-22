import flask
from ast import literal_eval as make_tuple
from flask import Flask, jsonify, request
from flask.views import MethodView
import psycopg2
import traceback
from datetime import datetime
import sys
sys.path.insert(0, '/var/www/')
import encrypt as encrypt_functions

app = Flask(__name__)

conn = psycopg2.connect(dbname="shopping_collaborator", user="www-data")

def home():
    return jsonify({'home': 'This is the homepage'}), 200

class UserAPI(MethodView):
    def get(self, uid):
        auth = str(request.headers.get('Token'))
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

        Response
        {
            'uid':<uid>
        }
        """
        auth = str(request.headers.get('Token'))
        if auth != '5c8ab94e-3c95-40f9-863d-e31ae49e5d8d':
            response = flask.Response(status=403)
            return response

        json = request.get_json()
        first_name = json['first_name']
        last_name = json['last_name']
        email = json['email']
        password = json['password']
        encrypted_password = encrypt_functions.encrypt(password)
        dt = datetime.now()
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO users (first_name, last_name, email, password, created, last_modified) VALUES (%s, %s, %s, %s, %s, %s) RETURNING uid;", (first_name, last_name, email, encrypted_password, dt, dt))
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
        auth = str(request.headers.get('Token'))
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
            encrypted_password = encrypt_functions.encrypt(password)
            values_to_update['password'] = encrypted_password

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
        auth = str(request.headers.get('Token'))
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
        auth = str(request.headers.get('Token'))
        if auth != '5c8ab94e-3c95-40f9-863d-e31ae49e5d8d':
            response = flask.Response(status=403)
            return response

        uid = request.args.get("uid")
        cur = conn.cursor()
        cur.execute("SELECT (group_user_match.gid, groups.group_name) FROM group_user_match INNER JOIN groups ON group_user_match.gid = groups.gid WHERE group_user_match.uid=%s", (uid,))
        data = {'groups' : []}
        for row in cur:
            components = row[0].split(',')
            components[0] = components[0].replace('(', '')
            components[0] = int(components[0])
            components[1] = components[1].replace('"', '')
            components[1] = components[1].replace(')','')
            row_data = {'gid':components[0], 'group_name':components[1]}
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
        auth = str(request.headers.get('Token'))
        if auth != '5c8ab94e-3c95-40f9-863d-e31ae49e5d8d':
            response = flask.Response(status=403)
            return response

        cur = conn.cursor()
        json = request.get_json()
        group_name = json["group_name"]
        uid = json["uid"]
        date = datetime.now()
        cur.execute("INSERT INTO groups (group_name, owner_uid, created, last_modified) VALUES (%s, %s, %s, %s) RETURNING gid;", (group_name, uid, date, date))
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
        auth = str(request.headers.get('Token'))
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
        uid = request.args.get("uid")
        uid = int(uid)
        auth = str(request.headers.get('Token'))
        if auth != '5c8ab94e-3c95-40f9-863d-e31ae49e5d8d':
            response = flask.Response(status=403)
            return response

        cur = conn.cursor()
        cur.execute("SELECT (owner_uid) FROM groups WHERE gid = %s;",(gid,))
        owner_uid = cur.fetchone()[0]
        if uid != owner_uid:
            response = flask.Response(status=401)
            return response;        
        cur.execute("DELETE FROM groups WHERE gid = %s;", (gid,))
        cur.execute("DELETE FROM group_user_match WHERE gid = %s;", (gid,))
        cur.execute("DELETE FROM items WHERE gid = %s", (gid,))
        conn.commit()
        cur.close()
        response = flask.Response(status=204)
        return response
    
class ItemsAPI(MethodView):
    def get(self):
        auth = str(request.headers.get('Token'))
        if auth != '5c8ab94e-3c95-40f9-863d-e31ae49e5d8d':
            response = flask.Response(status=403)
            return response

        gid = request.args.get("gid")
        cur = conn.cursor()
        cur.execute("SELECT (users.first_name, users.last_name, items.id, items.item_name, items.estimate) FROM items INNER JOIN users ON users.uid = items.uid WHERE items.gid=%s and items.done=%s;", (gid, False))
        data = {'items' : []}
        for row in cur:
            components = row[0].split(',')
            for i in range(0, len(components)):
                components[i] = components[i].replace('(', '')
                components[i] = components[i].replace('\"', '')
                components[i] = components[i].replace(')', '')
            row_data = {'first_name':components[0], 'last_name':components[1], 'item_id': components[2], 'item_name':components[3], 'estimate':components[4]}
            data['items'].append(row_data)
        cur.close()
        return jsonify(data), 200

    def post(self):
        """
        {
         "uid":<uid>
         "gid":<gid>
         "item_name":<item_name>
         "estimate":<estimate>
        }
        """
        auth = str(request.headers.get('Token'))
        if auth != '5c8ab94e-3c95-40f9-863d-e31ae49e5d8d':
            response = flask.Response(status=403)
            return response

        cur = conn.cursor()
        json = request.get_json()
        uid = json["uid"]
        gid = json["gid"]
        item_name = json["item_name"]
        estimate = json["estimate"]
        actual = 0.00
        done = False
        date = datetime.now()
        cur.execute("INSERT INTO items (gid, uid, item_name, estimate, actual, done, created, last_modified) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;", (gid, uid, item_name, estimate, actual, done, date, date))
        item_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        return jsonify({"id": item_id}), 201
    
    def put(self, item_id):
        """
        {
        "item_name": <item_name>
        "estimate": <estimate>
        "actual":<actual>
        "done":<boolean>
        }
        """
        auth = str(request.headers.get('Token'))
        if auth != '5c8ab94e-3c95-40f9-863d-e31ae49e5d8d':
            response = flask.Response(status=403)
            return response

        cur = conn.cursor()
        json = request.get_json()
        item_name = json["item_name"]
        estimate = json["estimate"]
        actual = json["actual"]
        done = json["done"]
        date = datetime.now()
        cur.execute("UPDATE items SET item_name = %s, estimate = %s, actual = %s, done = %s, last_modified = %s WHERE id = %s;", (item_name, estimate, actual, done, date, item_id))
        conn.commit()
        cur.close()
        response = flask.Response(status=204)
        return response

    def delete(self):
        auth = str(request.headers.get('Token'))
        if auth != '5c8ab94e-3c95-40f9-863d-e31ae49e5d8d':
            response = flask.Response(status=403)
            return response
        cur = conn.cursor()
        item_id_numbers = request.args.getlist("item_id")
        # if type(item_id_numbers) != list:
        #     cur.execute("DELETE FROM items WHERE id=%s", (item_id_numbers,))
        # else:
        #     for item_id in item_id_numbers:
        #         cur.execute("DELETE FROM items WHERE id=%s", (item_id,))
        # conn.commit()
        cur.close()
        # response = flask.Response(status=204)
        data = {'data':str(item_id_numbers), 'type':type(item_id_numbers)}
        return data, 200
    
class GroupUserAPI(MethodView):
    def get(self):
        auth = str(request.headers.get('Token'))
        if auth != '5c8ab94e-3c95-40f9-863d-e31ae49e5d8d':
            response = flask.Response(status=403)
            return response

        gid = request.args.get("gid")
        cur = conn.cursor()

        cur.execute("SELECT (users.uid, users.first_name, users.last_name) FROM users INNER JOIN (SELECT (group_user_match.uid) FROM group_user_match WHERE gid=%s) users_in_group ON users.uid = users_in_group.uid;", (gid,))
        
        data = {'users':[]}
        for row in cur:
            components = row[0].split(',')
            components[0] = components[0].replace('(', '')
            components[0] = int(components[0])
            components[2] = components[2].replace(')', '')
            row_data = {'uid':components[0], 'first_name':components[1], 'last_name':components[2]}
            data['users'].append(row_data)
        return jsonify(data), 200

    def post(self):
        """
        {
        "gid":<gid>
        "user_email":<user_email>
        }
        """
        auth = str(request.headers.get('Token'))
        if auth != '5c8ab94e-3c95-40f9-863d-e31ae49e5d8d':
            response = flask.Response(status=403)
            return response

        cur = conn.cursor()
        json = request.get_json()
        gid = json["gid"]
        user_email = json["user_email"]
        dt = datetime.now()
        cur.execute("SELECT (uid) FROM users WHERE email = %s;", (user_email,))
        row = cur.fetchone()
        if(row is None):
            return jsonify({"error": "user not found"}), 400
        uid = row[0]
        cur.execute("INSERT INTO group_user_match (gid, uid, created, last_modified) VALUES (%s, %s, %s, %s);", (gid, uid, dt, dt))
        conn.commit()
        cur.close()
        response = flask.Response(status=201)
        return response

    def delete(self):
        auth = str(request.headers.get('Token'))
        if auth != '5c8ab94e-3c95-40f9-863d-e31ae49e5d8d':
            response = flask.Response(status=403)
            return response

        cur = conn.cursor()
        gid = request.args.get("gid")
        uid = request.args.get("uid")
        uid = int(uid)
        cur.execute("SELECT (owner_uid) FROM groups WHERE gid = %s;",(gid,))
        owner_uid = cur.fetchone()[0]
        if uid == owner_uid:
            response = flask.Response(status=400)
            return response

        cur.execute("SELECT COUNT(*) FROM group_user_match WHERE gid = %s;", (gid,))
        count = int(cur.fetchone()[0])
        if count == 1:
            cur.execute("DELETE FROM groups WHERE gid = %s;", (gid,))
            conn.commit()
            cur.execute("DELETE FROM items WHERE gid = %s;", (gid,))
            conn.commit()
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
    auth = str(request.headers.get('Token'))
    if auth != '5c8ab94e-3c95-40f9-863d-e31ae49e5d8d':
        response = flask.Response(status=403)
        return response

    json = request.get_json()
    email = json['email']
    password = json['password']
    encrypted_password = encrypt_functions.encrypt(password)
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email = %s AND password = %s;", (email, encrypted_password))
    row = cur.fetchone()
    if row is None:
        response = flask.Response(status=401)
        return response
    cur.close()
    data = {'uid':row[0]}
    return jsonify(data), 200

def delete_items_group():
    auth = str(request.headers.get('Token'))
    if auth != '5c8ab94e-3c95-40f9-863d-e31ae49e5d8d':
        response = flask.Response(status=403)
        return response
    cur = conn.cursor()
    gid = request.args.get("gid")
    uid = request.args.get("uid")
    uid = int(uid)
    cur.execute("SELECT (owner_uid) FROM groups WHERE gid = %s;",(gid,))
    owner_uid = cur.fetchone()[0]
    if uid != owner_uid:
        response = flask.Response(status=401)
        return response;
    cur.execute("DELETE FROM items WHERE gid=%s", (gid,))
    conn.commit()
    cur.close()
    response = flask.Response(status=204)
    return response

def add_total_price():
    auth = str(request.headers.get('Token'))
    if auth != '5c8ab94e-3c95-40f9-863d-e31ae49e5d8d':
        response = flask.Response(status=403)
        return response
    cur = conn.cursor()
    gid = request.args.get("gid")
    cur.execute("SELECT (actual) FROM items WHERE gid = %s and done = %s", (gid, True))
    total = 0.0
    for row in cur:
        total += row[0]
    total_string = "{0:.2f}".format(total)
    data = {'total': total_string}
    return jsonify(data), 200

def items_complete_count():
    auth = str(request.headers.get('Token'))
    if auth != '5c8ab94e-3c95-40f9-863d-e31ae49e5d8d':
        response = flask.Response(status=403)
        return response
    cur = conn.cursor()
    gid = request.args.get("gid")

    cur.execute("SELECT COUNT(*) FROM items WHERE gid = %s", (gid,))
    total_items = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM items WHERE gid = %s and done = %s", (gid, True))
    complete_items = cur.fetchone()[0]

    data = {'items_bought': complete_items, 'total_items': total_items}
    return jsonify(data), 200


app.add_url_rule('/', 'home', home, methods=['GET'])
app.add_url_rule('/validate_user', 'validate_user', validate_user, methods=['POST'])
app.add_url_rule('/items/delete_all', 'delete_items_group', delete_items_group, methods=['DELETE'])
app.add_url_rule('/add_total_price', 'add_total_price', add_total_price, methods=['GET'])
app.add_url_rule('/items_completed', 'items_completed', items_complete_count, methods=['GET'])

user_view = UserAPI.as_view('user_api')
app.add_url_rule('/users/', view_func=user_view, methods=['POST',])
app.add_url_rule('/users/<int:uid>', view_func=user_view, methods=['GET','PUT', 'DELETE'])

group_view = GroupAPI.as_view('group_api')
app.add_url_rule('/groups', view_func=group_view, methods=['GET'])
app.add_url_rule('/groups/', view_func=group_view, methods=['POST',])
app.add_url_rule('/groups/<int:gid>', view_func=group_view, methods=['PUT', 'DELETE'])

item_view = ItemsAPI.as_view('item_view')
app.add_url_rule('/items', view_func=item_view, methods=['POST', 'GET', 'DELETE'])
app.add_url_rule('/items/<int:item_id>', view_func=item_view, methods=['PUT'])

group_user_view = GroupUserAPI.as_view('group_user_api')
app.add_url_rule('/group_user', view_func=group_user_view, methods=['GET', 'POST', 'DELETE'])

if __name__ == "__main__":
    app.run()
