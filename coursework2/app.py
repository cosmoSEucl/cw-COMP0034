from coursework2.gla_grants_app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)