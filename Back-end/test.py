from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route('/api/endpoint', methods=['POST'])
def handle_request():
    data = request.json  # 获取前端发送的JSON数据
    # 处理数据和业务逻辑
    print(data)
    response_data = {'message': 'Success'}
    return jsonify(response_data)

@app.route('/')
def hello():
    return 'Hello, Flask!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)