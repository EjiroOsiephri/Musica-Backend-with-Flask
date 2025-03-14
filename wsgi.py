from app import create_app

app = create_app()

@app.route('/')
def home():
    return "Hello, Flask over HTTPS!"

if __name__ == "__main__":
    app.run(ssl_context=('cert.pem', 'key.pem'), port=5000, debug=True)
