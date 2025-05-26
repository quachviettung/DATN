from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import re
import os

app = Flask(__name__)
CORS(app)  # Cho phép CORS để frontend gọi API

# Hàm kiểm tra đầu vào để đảm bảo an toàn
def is_valid_target(target):
    # Chỉ cho phép IPv4, IPv6, hoặc tên miền đơn giản
    ip_pattern = re.compile(r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$|^([a-fA-F0-9:]+:+)+[a-fA-F0-9]+$|^[a-zA-Z0-9.-]+$")
    return ip_pattern.match(target)

@app.route('/scan', methods=['POST'])
def scan():
    data = request.get_json()
    target = data.get('target')
    scan_type = data.get('scan_type', 'quick')  # Mặc định là quét nhanh

    if not target or not is_valid_target(target):
        return jsonify({'error': 'Mục tiêu không hợp lệ!'}), 400

    # Xây dựng lệnh Nmap dựa trên loại quét
    nmap_cmd = ['nmap']
    if scan_type == 'quick':
        nmap_cmd.extend(['-F'])  # Quét nhanh
    elif scan_type == 'full':
        nmap_cmd.extend(['-p-'])  # Quét tất cả cổng
    elif scan_type == 'stealth':
        nmap_cmd.extend(['-sS'])  # Quét SYN ẩn
    elif scan_type == 'service':
        nmap_cmd.extend(['-sV'])  # Phát hiện dịch vụ
    elif scan_type == 'os':
        nmap_cmd.extend(['-O'])  # Phát hiện OS
    elif scan_type == 'script':
        nmap_cmd.extend(['-sC'])  # Chạy script NSE
    nmap_cmd.append(target)

    try:
        # Chạy lệnh Nmap
        result = subprocess.run(nmap_cmd, capture_output=True, text=True, timeout=300)
        output = result.stdout
        if result.stderr:
            return jsonify({'error': 'Lỗi khi chạy Nmap: ' + result.stderr}), 500
        
        return jsonify({'output': output})
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Quét Nmap vượt quá thời gian chờ!'}), 500
    except Exception as e:
        return jsonify({'error': f'Lỗi không xác định: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)