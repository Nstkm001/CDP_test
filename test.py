from mitmproxy.tools.main import mitmdump

import requests
import json

def connect_debugger():
    connect_url = "http://localhost:3000/connect"
    connect_data = {
        "wsUrl": "ws://127.0.0.1:9222/devtools/page/9B37E91EFE7AB6C6B3F343A80B8FEFE2"
    }
    connect_headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(connect_url, headers=connect_headers, data=json.dumps(connect_data))
    return response

def evaluate_expression(expression):
    evaluate_url = "http://localhost:3000/evaluate"
    evaluate_data = {
        "expression": expression
    }
    evaluate_headers = {
        "Content-Type": "application/json"
    }

    response = requests.post(evaluate_url, headers=evaluate_headers, data=json.dumps(evaluate_data))
    return response.json()


def sign(data):
    print(data)
    recv = evaluate_expression(f"g.a.sm3('{data}')")
    print(recv)
    return recv.get('result').get('value')

def encrypt(data):
    print(data)
    recv = evaluate_expression(f"Object(h[\"b\"])({data})")
    print(recv)
    return recv.get('result').get('value')

def decrypt(data):
    print(data)
    recv = evaluate_expression(f"Object(h[\"a\"])({data})")
    print(recv)
    return recv.get('result').get('value')


def JSON_stringify(data):
    return json.dumps((data),separators=(",", ":"))


class MyAddon:
    @staticmethod
    def request(flow):
        if "process.json" in flow.request.path :
            datas = flow.request.get_content()
            datas = json.loads(datas)
            headers = flow.request.headers

            datas["signKey"] = sign(str(datas["sysHead"]["seqNo"]) + JSON_stringify(datas["sysHead"])+ JSON_stringify(datas["body"]) +"9tNFWyQNaXcWcjY9")
            datas["body"] = encrypt(JSON_stringify(datas["body"]))

            req_datas = JSON_stringify(datas).encode()
            Content_Length = bytes(str(len(req_datas)), 'utf-8')
            headers['Content-Length'] = Content_Length
            flow.request.raw_content = req_datas


    @staticmethod
    def response(flow):
        if flow.request.path == '/prod-api/at/AAS-aas/PublicTransaction/process.json?version=1.0.0':
            if b"body" in flow.response.get_content():
                datas = flow.response.get_content()
                datas = json.loads(datas)
                datas['a_test'] = json.loads(decrypt(JSON_stringify(datas["body"])))
                #避免其他的\被转化。
                req_datas = JSON_stringify(datas).replace("\\\"","\\\\\"").encode('utf-8').decode('unicode_escape')
                Content_Length = bytes(str(len(req_datas)), 'utf-8')
                headers = flow.response.headers
                headers['Content-Length'] = Content_Length
                flow.response.raw_content = req_datas

addons = [MyAddon()]

if __name__ == "__main__":
    connect_response = connect_debugger()

    if "error" not in connect_response:
        input("请点击触发断点后回车")
        expression = "g.a.sm3(a.sysHead.seqNo + JSON.stringify(a.sysHead) + JSON.stringify(t) + v).toString()"
        evaluate_response = evaluate_expression(expression)
        print("调用测试结果:",evaluate_response.get('result').get('value'))
        mitmdump(['-s', __file__, '--listen-host', '127.0.0.1', '--listen-port', '8899'])
    else:
        print("Failed to connect to debugger.")
