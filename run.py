from app import create_app, create_admin

app = create_app()
# Ensure the Flask app context is set up
app.app_context().push()


if __name__ == '__main__':
    create_admin() #calls the method to create Admin login details for managing HR Sign up.
    app.run(debug=True, port=5000, use_reloader=False)
