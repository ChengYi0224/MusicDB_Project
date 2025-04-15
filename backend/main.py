from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'

# 程式入口
if __name__ == "__main__":
    app.run(debug=True)