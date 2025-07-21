from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user, login_user
import json
import os
from minting import mint_erc20, mint_debt_nft, mint_offset_nft
from models import MintQueue, db, MintedToken
from datetime import datetime
import web3
from web3 import Web3
views = Blueprint("views", __name__)

CID_DID_PATH = "data/cid_did.json"

# Bắt buộc đăng nhập khi vào bất kỳ route nào (trừ login/register)
@views.before_app_request
def require_login():
    allowed_routes = ['views.login', 'register', 'static']
    if not current_user.is_authenticated and request.endpoint not in allowed_routes:
        return redirect(url_for('views.login'))

@views.route("/")
@login_required
def dashboard():
    queue_items = MintQueue.query.order_by(MintQueue.timestamp.asc()).all()
    # Đọc dữ liệu CID/DID
    if os.path.exists(CID_DID_PATH):
        with open(CID_DID_PATH, "r") as f:
            cid_did_records = json.load(f)
    else:
        cid_did_records = []
    return render_template("dashboard.html", queue_items=queue_items, cid_did_records=cid_did_records)

@views.route("/cid-did")
@login_required
def list_cid_did():
    if os.path.exists(CID_DID_PATH):
        with open(CID_DID_PATH, "r") as f:
            records = json.load(f)
    else:
        records = []
    return render_template("list_cid_did.html", records=records)

# Hàm tiện ích xóa cid/did, KHÔNG phải route
def remove_cid_did(cid, did):
    if os.path.exists(CID_DID_PATH):
        with open(CID_DID_PATH, "r") as f:
            records = json.load(f)
        records = [r for r in records if not (r.get("cid") == cid and r.get("did") == did)]
        with open(CID_DID_PATH, "w") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)

@views.route("/mint", methods=["POST"])
@login_required
def mint():
    did = request.form.get("did")
    cid = request.form.get("cid")
    type_raw = request.form.get("type")
    address = request.form.get("address")

    type_map = {
        "emitter_co2_log": "debt",
        "absorber_co2_log": "offset"
    }

    type_ = type_map.get(type_raw)
    if not type_:
        return jsonify({"error": f"Loại token không hợp lệ: {type_raw}"}), 400

    if not Web3.is_address(address):
        return jsonify({"error": "Địa chỉ ví không hợp lệ"}), 400

    try:
        if type_ == "debt":
            tx_hash = mint_debt_nft(address, cid, did)
        elif type_ == "offset":
            tx_hash = mint_offset_nft(address, cid, did)
        else:
            return jsonify({"error": f"Không xác định được loại mint: {type_}"}), 400
        # Lưu vào bảng MintedToken
        minted = MintedToken(
            token_type=type_,
            wallet=address,
            cid=cid,
            did=did,
            tx_hash=tx_hash,
            token_id="pending",
            timestamp=datetime.utcnow()
        )
        db.session.add(minted)
        db.session.commit()
        remove_cid_did(cid, did)  # Xoá khỏi file sau khi mint thành công
        return jsonify({"message": "Success", "tx_hash": tx_hash}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@views.route("/api/save_cid_did", methods=["POST"])
def save_cid_did():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing data"}), 400

    if os.path.exists(CID_DID_PATH):
        with open(CID_DID_PATH, "r") as f:
            all_data = json.load(f)
    else:
        all_data = []

    all_data.append(data)

    with open(CID_DID_PATH, "w") as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)

    # Lưu vào hàng chờ nếu chưa có
    new_item = MintQueue(
        wallet=data.get("wallet", ""),
        cid=data.get("cid"),
        did=data.get("did"),
        token_type=data.get("type"),
        timestamp=datetime.utcnow()
    )
    db.session.add(new_item)
    db.session.commit()

    return jsonify({"status": "success", "message": "CID + DID received"}), 200

@views.route("/mint_from_dashboard", methods=["POST"])
@login_required
def mint_from_dashboard():
    type_raw = request.form.get("type")
    type_map = {
        "emitter_co2_log": "debt",
        "absorber_co2_log": "offset"
    }
    type_ = type_map.get(type_raw)
    if type_ is None:
        return jsonify({"error": f"Loại token không hợp lệ: {type_raw}"}), 400

    wallet_address = request.form.get("wallet_address")
    did = request.form.get("did")
    cid = request.form.get("cid")

    try:
        if type_ == "debt":
            tx_hash = mint_debt_nft(wallet_address, cid, did)
        elif type_ == "offset":
            tx_hash = mint_offset_nft(wallet_address, cid, did)
        else:
            return jsonify({"error": f"Không xác định được loại mint: {type_}"}), 400

        return jsonify({"status": "success", "tx_hash": tx_hash}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@views.route("/mint_from_queue/<int:queue_id>", methods=["POST"])
@login_required
def mint_from_queue(queue_id):
    item = MintQueue.query.get(queue_id)
    if not item:
        flash("Không tìm thấy mục hàng chờ", "danger")
        return redirect(url_for("views.dashboard"))

    wallet = request.form["wallet"]

    try:
        if item.token_type == "debt":
            tx_hash = mint_debt_nft(wallet, item.cid, item.did)
        elif item.token_type == "offset":
            tx_hash = mint_offset_nft(wallet, item.cid, item.did)
        else:
            raise Exception("Loại token không hợp lệ")

        minted = MintedToken(
            token_type=item.token_type,
            wallet=wallet,
            cid=item.cid,
            did=item.did,
            tx_hash=tx_hash,
            token_id="pending"
        )
        db.session.add(minted)
        db.session.delete(item)
        db.session.commit()

        flash(f"Mint thành công! Tx hash: {tx_hash}", "success")
    except Exception as e:
        flash(f"Lỗi mint từ hàng chờ: {e}", "danger")

    return redirect(url_for("views.dashboard"))

@views.route("/minted_tokens")
@login_required
def minted_tokens():
    search = request.args.get("search", "")
    if search:
        tokens = MintedToken.query.filter(
            (MintedToken.cid.contains(search)) | (MintedToken.did.contains(search))
        ).order_by(MintedToken.timestamp.desc()).all()
    else:
        tokens = MintedToken.query.order_by(MintedToken.timestamp.desc()).all()
    # Hiển thị danh sách CID nếu là nhiều CID
    for t in tokens:
        try:
            import json
            t.cid_list = json.loads(t.cid)
        except:
            t.cid_list = [t.cid]
    return render_template("minted_tokens.html", tokens=tokens)

@views.route("/login", methods=["GET", "POST"])
def login():
    # Nếu đã đăng nhập thì chuyển về dashboard
    if current_user.is_authenticated:
        return redirect(url_for("views.dashboard"))
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        # Đọc từ .env
        import os
        admin_user = os.getenv("ADMIN_USERNAME", "admin")
        admin_pass = os.getenv("ADMIN_PASSWORD", "123456")
        if username == admin_user and password == admin_pass:
            from user import AdminUser
            login_user(AdminUser())
            flash("Đăng nhập thành công!", "success")
            return redirect(url_for("views.dashboard"))
        else:
            flash("Sai tên đăng nhập hoặc mật khẩu!", "danger")
    return render_template("login.html")

@views.route("/bulk_mint", methods=["POST"])
@login_required
def bulk_mint():
    wallet = request.form.get("bulk_wallet")
    selected = request.form.getlist("bulk_selected")
    errors = []
    # Gom các cid/did theo type
    debt_cids = []
    offset_cids = []
    did_debt = None
    did_offset = None
    for entry in selected:
        cid, did, type_ = entry.split("|")
        if type_ == "debt":
            debt_cids.append(cid)
            did_debt = did
        elif type_ == "offset":
            offset_cids.append(cid)
            did_offset = did
        else:
            errors.append(f"Sai type cho {cid} {did}")
    # Mint 1 NFT chứa nhiều cid cho mỗi type
    minted_count = 0
    if debt_cids:
        try:
            tx_hash = mint_debt_nft(wallet, debt_cids, did_debt)
            # Lưu MintedToken với danh sách CID
            import json
            minted = MintedToken(
                token_type="debt",
                wallet=wallet,
                cid=json.dumps(debt_cids),
                did=did_debt,
                tx_hash=tx_hash,
                token_id="pending",
                timestamp=datetime.utcnow()
            )
            db.session.add(minted)
            minted_count += 1
        except Exception as e:
            errors.append(f"Debt: {e}")
    if offset_cids:
        try:
            tx_hash = mint_offset_nft(wallet, offset_cids, did_offset)
            import json
            minted = MintedToken(
                token_type="offset",
                wallet=wallet,
                cid=json.dumps(offset_cids),
                did=did_offset,
                tx_hash=tx_hash,
                token_id="pending",
                timestamp=datetime.utcnow()
            )
            db.session.add(minted)
            minted_count += 1
        except Exception as e:
            errors.append(f"Offset: {e}")
    db.session.commit()
    # Xoá các cid/did đã mint khỏi file
    for entry in selected:
        cid, did, type_ = entry.split("|")
        remove_cid_did(cid, did)
    if minted_count:
        flash(f"Mint thành công {minted_count} NFT (mỗi loại 1 NFT chứa nhiều CID)!", "success")
    if errors:
        flash("; ".join(errors), "danger")
    return redirect(url_for("views.dashboard"))

@views.route("/bulk_mint_page")
@login_required
def bulk_mint_page():
    if os.path.exists(CID_DID_PATH):
        with open(CID_DID_PATH, "r") as f:
            cid_did_records = json.load(f)
    else:
        cid_did_records = []
    return render_template("bulk_mint.html", cid_did_records=cid_did_records)

@views.route("/manual_mint_page")
@login_required
def manual_mint_page():
    if os.path.exists(CID_DID_PATH):
        with open(CID_DID_PATH, "r") as f:
            cid_did_records = json.load(f)
    else:
        cid_did_records = []
    return render_template("manual_mint.html", cid_did_records=cid_did_records)


