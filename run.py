from app import app, db

# Ensure app context is set up
app.app_context().push()

# Create the database tables
db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
