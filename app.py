# e6i3a575h 2pg7oejii
from flask import (
    Flask,
    render_template,
    request,
    session,
    redirect,
    url_for,
    jsonify,
    g,
) ####
from flask_socketio import SocketIO, send, emit
from flask_cors import CORS
import psycopg2
import psycopg2
from psycopg2.extras import RealDictCursor, DictCursor
from traceback import format_exc
from psycopg2 import extras  # Add this line

app = Flask(__name__)
CORS(app,resources={r"/*": {"origins": "https://poll-gtp.vercel.app"}})
app.secret_key = "buTTerfly@23"

"""
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASS = "123"
DB_HOST = "localhost"
DB_PORT = "5432"
db_uri = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

"""
end_point_ID = "ep-tiny-brook-36213830-pooler"
DB_NAME = "verceldb"
DB_USER = "default"
DB_PASS = "z7Hod5jFraZU"
DB_HOST = f"{end_point_ID}.us-east-1.postgres.vercel-storage.com"
DB_PORT = "5432"
db_uri = "postgres://default:4P9oyZKdhgav@ep-proud-meadow-45284793.us-east-1.postgres.vercel-storage.com:5432/verceldb?sslmode=require&options=endpoint%3Dep-proud-meadow-45284793-pooler"


global conn
try:
    # Connect to the database
    with psycopg2.connect(db_uri) as conn:
        print("Database connected successfully")

        # Create a cursor
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Create "user" table
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS "user" (
                    username VARCHAR(80) NOT NULL PRIMARY KEY,
                    vote INTEGER NOT NULL DEFAULT 0
                );
            """
            )

            # Create "help" table
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS help (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(80) NOT NULL
                );
            """
            )

        # Commit the changes
        conn.commit()

except Exception as e:
    # Handle exceptions
    print(f"Error: {e}")


@app.route("/")
def home():
    if "username" in session:
        username = session["username"]
        return render_template("logged.html", username=username)
    return 'You are not logged in | <a href="/login">Login</a>'


@app.before_first_request
def before_first_request():
    create_connection()
    create_tables()


@app.route("/login", methods=["GET", "POST"])
def login():
    global conn  # Declare conn as a global variable within the function

    if request.method == "POST":
        username = request.form["username"]
        try:
            # Check if the connection is closed and reopen it if necessary
            if conn.closed:
                initialize_connection()

            # Open a new cursor using the connection
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Check if the username already exists
                cur.execute('SELECT * FROM "user" WHERE username = %s', (username,))
                existing_user = cur.fetchone()

                if existing_user:
                    # User already exists, handle accordingly (e.g., show error message)
                    session["username"] = username
                    return redirect(url_for("home"))

                # User does not exist, proceed with the insertion
                cur.execute(
                    'INSERT INTO "user" (username, vote) VALUES (%s, %s)',
                    (username, 0),
                )

            # Commit changes outside the with block
            conn.commit()

            session["username"] = username
            return redirect(url_for("home"))
        except Exception as e:
            print(f"Error: {e}")
            return jsonify({"error": "Internal Server Error"}), 500

    return render_template("login.html")


def create_connection():
    # Create a new connection to the database
    return psycopg2.connect(db_uri)


@app.route("/help_data")
def help_data():
    global conn  # Declare conn as a global variable within the function

    try:
        # Check if the connection is closed and reopen it if necessary
        if conn.closed:
            conn = create_connection()  # Replace with your create_connection function

        with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
            cur.execute('SELECT id, username FROM "help"')
            help_entries = cur.fetchall()
            data = [
                {"id": entry["id"], "username": entry["username"]}
                for entry in help_entries
            ]
        return render_template("help_data.html", data=data)

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Internal Server Error"}), 500


@app.route("/fetch_help_data")
def fetch_help_data():
    global conn, db_uri  # Declare conn and db_uri as global variables within the function

    try:
        # Check if the connection is closed and reopen it if necessary
        if conn.closed:
            conn = psycopg2.connect(db_uri)

        print("Fetching help data...")

        # Open a new cursor using the connection
        with conn.cursor() as cur:
            cur.execute("SELECT id, username FROM help")
            help_entries = cur.fetchall()
            data = [{"id": entry[0], "username": entry[1]} for entry in help_entries]
            print("Help data fetched successfully.")
            return jsonify(data)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Internal Server Error"}), 500


@app.route("/help", methods=["POST"])
def help():
    global conn  # Declare conn as a global variable within the function

    if "username" in session:
        current_username = session["username"]
        cur = None
        try:
            # Check if the connection is closed and reopen it if necessary
            if conn.closed:
                conn = (
                    create_connection()
                )  # Replace with your create_connection function

            # Open a new cursor using the connection
            with conn.cursor() as cur:
                # Assuming 'help' table exists with 'id' and 'username' columns
                cur.execute(
                    "INSERT INTO help (username) VALUES (%s)", (current_username,)
                )
                conn.commit()
                return jsonify({"message": "Help requested successfully"})
        except Exception as e:
            print(format_exc())  # Print the traceback
            return jsonify({"error": str(e)}), 500
        finally:
            if cur is not None:
                cur.close()
    return jsonify({"message": "User not logged in"})


@app.route("/delete_help_request/<int:help_id>", methods=["DELETE"])
def delete_help_request(help_id):
    try:
        with psycopg2.connect(db_uri) as conn:
            # Open a cursor using the connection
            with conn.cursor() as cur:
                # Execute SQL query to delete the help request with the specified ID
                cur.execute("DELETE FROM help WHERE id = %s", (help_id,))

            # Commit the changes
            conn.commit()

            # Check if any rows were affected (help request deleted)
            if cur.rowcount > 0:
                return jsonify({"message": "Help request deleted successfully"}), 200
            else:
                return jsonify({"error": "Help request not found"}), 404
    except Exception as e:
        print(format_exc())
        return jsonify({"error": str(e)}), 500


@app.route("/clear_all_help_requests", methods=["GET", "DELETE"])
def clear_all_help_requests():
    try:
        with psycopg2.connect(db_uri) as conn:
            # Open a cursor using the connection
            with conn.cursor() as cur:
                # Execute SQL query to delete all records from "help" table
                cur.execute('DELETE FROM "help"')
                cur.execute(
                    """
                    SELECT column_default
                    FROM information_schema.columns
                    WHERE table_name = 'help' AND column_name = 'id';
                """
                )
                result = cur.fetchone()

                if result and "nextval" in result[0]:
                    sequence_name = result[0].split("'")[1]
                    cur.execute(f"ALTER SEQUENCE {sequence_name} RESTART WITH 1")
            # Commit the changes
            conn.commit()

        return jsonify({"message": "All help requests cleared successfully"}), 200
    except Exception as e:
        print(format_exc())
        return jsonify({"error": str(e)}), 500


@app.route("/new_task")
def new_task():
    try:
        with psycopg2.connect(db_uri) as conn:
            # Open a cursor using the connection
            with conn.cursor() as cur:
                # Execute SQL query to delete all records from "help" table

                cur.execute(
                    """
                UPDATE "user"
                SET vote = 0;

                """
                )

            # Commit the changes
            conn.commit()

        return jsonify({"message": "New Task Assigned"}), 200
    except Exception as e:
        print(format_exc())
        return jsonify({"error": str(e)}), 500


ADMIN_ROUTE = f"/admin-{app.secret_key}"
print(ADMIN_ROUTE)


@app.route(ADMIN_ROUTE, methods=["GET"])
def admin():
    # This route is only accessible if the request contains the correct secret key
    return render_template("admin.html")


@app.route("/logout")
def logout():
    username = session.get("username")
    if username:
        try:
            execute_query('DELETE FROM "user" WHERE username = %s', (username,))
        except:
            print("User not in table")
    session.pop("username", None)
    return redirect(url_for("home"))

@app.route("/graph")
def graph():
    return render_template("graph.html")


def execute_query(query, params=None):
    with psycopg2.connect(db_uri) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params)
            return cur.fetchall()


@app.route("/get_votes_count")
def get_votes_count():
    try:
        # Assuming 'user' table exists with 'vote' column
        query_0 = 'SELECT COUNT(*) AS count_0 FROM "user" WHERE vote = 0'
        result_0 = execute_query(query_0)

        query_1 = 'SELECT COUNT(*) AS count_1 FROM "user" WHERE vote = 1'
        result_1 = execute_query(query_1)

        count_0 = result_0[0]["count_0"] if result_0 else 0
        count_1 = result_1[0]["count_1"] if result_1 else 0

        return jsonify({"0": count_0, "1": count_1})
    except psycopg2.Error as e:
        # Log the error details
        print(f"PostgreSQL Error: {e}")
        return jsonify({"error": "Internal Server Error"}), 500
    except Exception as e:
        # Log other exceptions
        print(f"Unexpected Error: {e}")
        return jsonify({"error": "Internal Server Error"}), 500


@app.route("/submit_vote", methods=["POST"])
def submit_vote_socketio():
    if request.method == "POST":
        current_username = session.get("username")
        query_update_vote = """UPDATE "user" SET vote = 1 WHERE username = %s"""

        try:
            # Create a new connection
            with psycopg2.connect(db_uri) as conn:
                # Open a new cursor using the connection
                with conn.cursor() as cur:
                    cur.execute(query_update_vote, (current_username,))
                    conn.commit()  # Commit changes within the same context

            return jsonify({"message": "Voted successfully"})

        except Exception as e:
            print(f"Exception: {e}")
            print(format_exc())  # Print the traceback
            return jsonify({"error": str(e)}), 500

    return jsonify({"message": "Not Voted"})


@app.route("/delete_all_users_page")
def delete_all_users_page():
    return render_template("delete_all_users.html")


# Initialize SocketIO
socketio = SocketIO(app)


def delete_all_users(conn):
    try:
        # Start a transaction
        conn.autocommit = False

        # Open a new cursor using the connection
        with conn.cursor() as cur:
            # Use psycopg2 to delete all users
            query_delete_users = 'DELETE FROM "user"'
            cur.execute(query_delete_users)
            conn.commit()

        # Broadcast a logout event to all connected clients
        socketio.emit("logout_all_clients", namespace="/")

        # Return success response
        return jsonify({"message": "All users deleted successfully"}), 200
    except Exception as e:
        # Rollback the transaction in case of an error
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        # Set autocommit back to True to end the transaction
        conn.autocommit = True


@app.route("/delete_all_users", methods=["GET", "POST"])
def delete_all_users_route():
    # Open a new connection to the database
    conn = create_connection()
    response = delete_all_users(conn)
    conn.close()  # Close the connection after use
    return response if response else ("", 204)
    

def create_tables():
    conn = None  # Initialize conn outside the try block

    try:
        conn = psycopg2.connect(db_uri)
        print("Database connected successfully")

        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Create tables using psycopg2
            query_create_users_table = """
            CREATE TABLE IF NOT EXISTS "user" (
                id SERIAL PRIMARY KEY,
                username VARCHAR(255),
                vote INTEGER
            )
            """
            cur.execute(query_create_users_table)

            query_create_help_table = """
            CREATE TABLE IF NOT EXISTS help (
                id SERIAL PRIMARY KEY,
                username VARCHAR(255)
            )
            """
            cur.execute(query_create_help_table)

            """
            # Delete all records in User and Help tables
            query_delete_users = 'DELETE FROM "user"'
            cur.execute(query_delete_users)
                                                            >>>>>> This will clear the database when the web app closed
            query_delete_help = "DELETE FROM help"
            cur.execute(query_delete_help)
            """

            # Commit the changes
            conn.commit()

    except Exception as e:
        # Rollback the transaction in case of an error
        if conn is not None:
            conn.rollback()
        print(f"Error: {str(e)}")

    finally:
        # Close the connection in the finally block to ensure it's always closed
        if conn is not None:
            conn.close()


@app.teardown_appcontext
def close_connection(exception=None):
    conn = getattr(g, "_database_conn", None)
    cur = getattr(g, "_database_cur", None)

    if conn is not None:
        conn.close()

    if cur is not None:
        cur.close()

