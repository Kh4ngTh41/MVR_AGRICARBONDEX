from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)
CID_DID_FILE = 'data/cid_did.json'

def save_to_file(entry):
    if not os.path.exists(CID_DID_FILE):
        with open(CID_DID_FILE, 'w') as f:
            json.dump([], f)
    with open(CID_DID_FILE, 'r+') as f:
        data = json.load(f)
        data.append(entry)
        f.seek(0)
        json.dump(data, f, indent=2)
        f.truncate()

@app.route('/api/save_cid_did', methods=['POST'])
def save_cid_did():
    req = request.get_json()
    if not req:
        return jsonify({"error": "No data provided"}), 400
    # Optional: kiểm tra hợp lệ
    required = ["did", "cid", "timestamp", "type"]
    if not all(k in req for k in required):
        return jsonify({"error": "Missing fields"}), 400

    # Mapping thêm ví từ DID (nếu có mapping sẵn), demo dùng cứng
    req['wallet'] = "0xReceiverWalletForThisDID"

    save_to_file(req)
    return jsonify({"status": "success"}), 200

if __name__ == '__main__':
    app.run(port=5002, debug=True)
