from mitmproxy.tools.main import mitmdump
import requests
import json


# 全局代理开关
USE_PROXY = True

# 全局代理配置
PROXIES = {
    "http": "http://127.0.0.1:8080",
    "https": "http://127.0.0.1:8080"
}

def evaluate_expression(expression):
    evaluate_url = "http://localhost:3000/evaluate"
    evaluate_data = {
        "expression": expression
    }
    evaluate_headers = {
        "Content-Type": "application/json"
    }

    # 根据全局开关决定是否使用代理
    proxies = PROXIES if USE_PROXY else None

    # 发送 POST 请求
    response = requests.post(
        evaluate_url,
        headers=evaluate_headers,
        data=json.dumps(evaluate_data),
        proxies=proxies  # 传入代理
    )
    return response.json()


def sign(data,requestId,timestamp):
    recv = evaluate_expression(f"a.a.MD5('{data}{requestId}{timestamp}').toString()")
    return recv.get('result').get('value')

def Get_requestId():
    recv = evaluate_expression(f"p()")
    return recv.get('result').get('value')

def Get_timestamp():
    recv = evaluate_expression(f"Date.parse(new Date)")
    return recv.get('result').get('description')

def encrypt(data):
    print(data)
    recv = evaluate_expression(f"l('{data}')")
    print(recv)
    return recv.get('result').get('value')

def decrypt(data):
    print(data)
    recv = evaluate_expression(f"d('{data}')")
    print(recv)
    return recv.get('result').get('value')

def JSON_stringify(data):
    return json.dumps((data),separators=(",", ":"),ensure_ascii=False)


class MyAddon:
    @staticmethod
    def request(flow):
        datas = flow.request.get_content()
        headers = flow.request.headers
        requestId = Get_requestId()
        timestamp = Get_timestamp()
        headers['requestId'] = requestId
        headers['timestamp'] = timestamp
        headers['sign'] = sign(str(datas.decode()),requestId,timestamp)
        req_datas = encrypt(str(datas.decode()))
        Content_Length = bytes(str(len(req_datas)), 'utf-8')
        headers['Content-Length'] = Content_Length
        flow.request.raw_content = req_datas.encode()


    @staticmethod
    def response(flow):
        datas = flow.response.get_content()
        datas = decrypt(datas.decode())
        #避免其他的\被转化。
        req_datas = json.loads(JSON_stringify(datas))
        Content_Length = bytes(str(len(req_datas)), 'utf-8')
        headers = flow.response.headers
        headers['Content-Length'] = Content_Length
        flow.response.raw_content = req_datas.encode()

addons = [MyAddon()]

if __name__ == "__main__":
    mitmdump(['-s', __file__, '--listen-host', '127.0.0.1', '--listen-port', '8899'])
