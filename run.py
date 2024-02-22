from app import app, db

# Ensure the Flask app context is set up
app.app_context().push()

# Optionally, create database tables if they don't exist
db.create_all()

if __name__ == '__main__':
    app.run(debug=True)