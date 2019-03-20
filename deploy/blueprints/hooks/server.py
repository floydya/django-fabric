import subprocess
from flask import Flask, request


app = Flask(__name__)


@app.route('/', methods=['POST', 'GET'])
def main():
    subprocess.call(['bash', 'update.sh'])
    return '200'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port='5000')
