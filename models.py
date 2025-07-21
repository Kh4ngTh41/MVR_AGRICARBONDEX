from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class MintedToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token_type = db.Column(db.String(50))
    wallet = db.Column(db.String(100))
    cid = db.Column(db.Text)  # Lưu list CID dạng chuỗi JSON
    did = db.Column(db.String(100))
    tx_hash = db.Column(db.String(100))
    token_id = db.Column(db.String(100))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def get_cid_list(self):
        try:
            import json
            return json.loads(self.cid)
        except:
            return [self.cid]

class MintQueue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cid = db.Column(db.String(255), nullable=False)
    did = db.Column(db.String(255), nullable=False)
    token_type = db.Column(db.String(10), nullable=False)  # "debt" hoặc "offset"
    wallet = db.Column(db.String(42), nullable=True)  # tuỳ chọn: ví người nhận
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)