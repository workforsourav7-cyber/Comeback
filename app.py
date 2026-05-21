import os
import json
from mitmproxy import http
from pathlib import Path
import sys
import requests
import base64
import secrets
import hashlib
import time
from datetime import datetime, timedelta
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder

UID_FILE = "uid.txt"
CERT_FILE = "certificat_mitmproxy.pem"
ACCESS_FILE = "access.txt"
BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# Create directories if not exist
TEMPLATES_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)
(STATIC_DIR / "css").mkdir(exist_ok=True)
(STATIC_DIR / "js").mkdir(exist_ok=True)

# Cache for UID to JWT mapping
uid_jwt_cache = {}
# Cache for access tokens
access_tokens = {}

# --- PROTOBUF FOR MAJORLOGIN ---
_sym_db = _symbol_database.Default()

DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x13MajorLoginReq.proto\"\xfa\n\n\nMajorLogin\x12\x12\n\nevent_time\x18\x03 \x01(\t\x12\x11\n\tgame_name\x18\x04 \x01(\t\x12\x13\n\x0bplatform_id\x18\x05 \x01(\x05\x12\x16\n\x0e\x63lient_version\x18\x07 \x01(\t\x12\x17\n\x0fsystem_software\x18\x08 \x01(\t\x12\x17\n\x0fsystem_hardware\x18\t \x01(\t\x12\x18\n\x10telecom_operator\x18\n \x01(\t\x12\x14\n\x0cnetwork_type\x18\x0b \x01(\t\x12\x14\n\x0cscreen_width\x18\x0c \x01(\r\x12\x15\n\rscreen_height\x18\r \x01(\r\x12\x12\n\nscreen_dpi\x18\x0e \x01(\t\x12\x19\n\x11processor_details\x18\x0f \x01(\t\x12\x0e\n\x06memory\x18\x10 \x01(\r\x12\x14\n\x0cgpu_renderer\x18\x11 \x01(\t\x12\x13\n\x0bgpu_version\x18\x12 \x01(\t\x12\x18\n\x10unique_device_id\x18\x13 \x01(\t\x12\x11\n\tclient_ip\x18\x14 \x01(\t\x12\x10\n\x08language\x18\x15 \x01(\t\x12\x0f\n\x07open_id\x18\x16 \x01(\t\x12\x14\n\x0copen_id_type\x18\x17 \x01(\t\x12\x13\n\x0b\x64\x65vice_type\x18\x18 \x01(\t\x12\'\n\x10memory_available\x18\x19 \x01(\x0b\x32\r.GameSecurity\x12\x14\n\x0c\x61\x63\x63\x65ss_token\x18\x1d \x01(\t\x12\x17\n\x0fplatform_sdk_id\x18\x1e \x01(\x05\x12\x1a\n\x12network_operator_a\x18) \x01(\t\x12\x16\n\x0enetwork_type_a\x18* \x01(\t\x12\x1c\n\x14\x63lient_using_version\x18\x39 \x01(\t\x12\x1e\n\x16\x65xternal_storage_total\x18< \x01(\x05\x12\"\n\x1a\x65xternal_storage_available\x18= \x01(\x05\x12\x1e\n\x16internal_storage_total\x18> \x01(\x05\x12\"\n\x1ainternal_storage_available\x18? \x01(\x05\x12#\n\x1bgame_disk_storage_available\x18@ \x01(\x05\x12\x1f\n\x17game_disk_storage_total\x18\x41 \x01(\x05\x12%\n\x1d\x65xternal_sdcard_avail_storage\x18\x42 \x01(\x05\x12%\n\x1d\x65xternal_sdcard_total_storage\x18\x43 \x01(\x05\x12\x10\n\x08login_by\x18I \x01(\x05\x12\x14\n\x0clibrary_path\x18J \x01(\t\x12\x12\n\nreg_avatar\x18L \x01(\x05\x12\x15\n\rlibrary_token\x18M \x01(\t\x12\x14\n\x0c\x63hannel_type\x18N \x01(\x05\x12\x10\n\x08\x63pu_type\x18O \x01(\x05\x12\x18\n\x10\x63pu_architecture\x18Q \x01(\t\x12\x1b\n\x13\x63lient_version_code\x18S \x01(\t\x12\x14\n\x0cgraphics_api\x18V \x01(\t\x12\x1d\n\x15supported_astc_bitset\x18W \x01(\r\x12\x1a\n\x12login_open_id_type\x18X \x01(\x05\x12\x18\n\x10\x61nalytics_detail\x18Y \x01(\x0c\x12\x14\n\x0cloading_time\x18\\ \x01(\r\x12\x17\n\x0frelease_channel\x18] \x01(\t\x12\x12\n\nextra_info\x18^ \x01(\t\x12 \n\x18\x61ndroid_engine_init_flag\x18_ \x01(\r\x12\x0f\n\x07if_push\x18\x61 \x01(\x05\x12\x0e\n\x06is_vpn\x18\x62 \x01(\x05\x12\x1c\n\x14origin_platform_type\x18\x63 \x01(\t\x12\x1d\n\x15primary_platform_type\x18\x64 \x01(\t\"5\n\x0cGameSecurity\x12\x0f\n\x07version\x18\x06 \x01(\x05\x12\x14\n\x0chidden_value\x18\x08 \x01(\x04\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'MajorLoginReq_pb2', _globals)
MajorLogin = _globals['MajorLogin']
GameSecurity = _globals['GameSecurity']

DESCRIPTOR2 = _descriptor_pool.Default().AddSerializedFile(b'\n\x13MajorLoginRes.proto\"|\n\rMajorLoginRes\x12\x13\n\x0b\x61\x63\x63ount_uid\x18\x01 \x01(\x04\x12\x0e\n\x06region\x18\x02 \x01(\t\x12\r\n\x05token\x18\x08 \x01(\t\x12\x0b\n\x03url\x18\n \x01(\t\x12\x11\n\ttimestamp\x18\x15 \x01(\x03\x12\x0b\n\x03key\x18\x16 \x01(\x0c\x12\n\n\x02iv\x18\x17 \x01(\x0c\x62\x06proto3')
_globals2 = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR2, _globals2)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR2, 'MajorLoginRes_pb2', _globals2)
MajorLoginRes = _globals2['MajorLoginRes']

# --- AES CONSTANTS ---
AES_KEY = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
AES_IV = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])

def encrypt_aes(data: bytes) -> bytes:
    cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
    return cipher.encrypt(pad(data, AES.block_size))

def build_major_login(open_id: str, access_token: str, platform_type: int) -> bytes:
    major = MajorLogin()
    major.event_time = "2025-03-23 12:00:00"
    major.game_name = "free fire"
    major.platform_id = 1
    major.client_version = "1.120.2"
    major.system_software = "Android OS 9 / API-28 (PQ3B.190801.10101846/G9650ZHU2ARC6)"
    major.system_hardware = "Handheld"
    major.telecom_operator = "Verizon"
    major.network_type = "WIFI"
    major.screen_width = 1920
    major.screen_height = 1080
    major.screen_dpi = "280"
    major.processor_details = "ARM64 FP ASIMD AES VMH | 2865 | 4"
    major.memory = 3003
    major.gpu_renderer = "Adreno (TM) 640"
    major.gpu_version = "OpenGL ES 3.1 v1.46"
    major.unique_device_id = "Google|34a7dcdf-a7d5-4cb6-8d7e-3b0e448a0c57"
    major.client_ip = "223.191.51.89"
    major.language = "en"
    major.open_id = open_id
    major.open_id_type = "4"
    major.device_type = "Handheld"
    major.memory_available.version = 55
    major.memory_available.hidden_value = 81
    major.access_token = access_token
    major.platform_sdk_id = 1
    major.network_operator_a = "Verizon"
    major.network_type_a = "WIFI"
    major.client_using_version = "7428b253defc164018c604a1ebbfebdf"
    major.external_storage_total = 36235
    major.external_storage_available = 31335
    major.internal_storage_total = 2519
    major.internal_storage_available = 703
    major.game_disk_storage_available = 25010
    major.game_disk_storage_total = 26628
    major.external_sdcard_avail_storage = 32992
    major.external_sdcard_total_storage = 36235
    major.login_by = 3
    major.library_path = "/data/app/com.dts.freefireth-YPKM8jHEwAJlhpmhDhv5MQ==/lib/arm64"
    major.reg_avatar = 1
    major.library_token = "5b892aaabd688e571f688053118a162b|/data/app/com.dts.freefireth-YPKM8jHEwAJlhpmhDhv5MQ==/base.apk"
    major.channel_type = 3
    major.cpu_type = 2
    major.cpu_architecture = "64"
    major.client_version_code = "2019118695"
    major.graphics_api = "OpenGLES2"
    major.supported_astc_bitset = 16383
    major.login_open_id_type = 4
    major.analytics_detail = b"FwQVTgUPX1UaUllDDwcWCRBpWA0FUgsvA1snWlBaO1kFYg=="
    major.loading_time = 13564
    major.release_channel = "android"
    major.extra_info = "KqsHTymw5/5GB23YGniUYN2/q47GATrq7eFeRatf0NkwLKEMQ0PK5BKEk72dPflAxUlEBir6Vtey83XqF593qsl8hwY="
    major.android_engine_init_flag = 110009
    major.if_push = 1
    major.is_vpn = 1
    major.origin_platform_type = str(platform_type)
    major.primary_platform_type = str(platform_type)
    return major.SerializeToString()

def decode_jwt(token: str) -> dict:
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return {}
        header = json.loads(base64.urlsafe_b64decode(parts[0] + '==').decode())
        payload = json.loads(base64.urlsafe_b64decode(parts[1] + '==').decode())
        return {"header": header, "payload": payload}
    except Exception as e:
        return {"error": str(e)}

def access_token_to_jwt(access_token: str):
    inspect_url = f"https://100067.connect.garena.com/oauth/token/inspect?token={access_token}"
    try:
        insp_resp = requests.get(inspect_url, timeout=10)
        if insp_resp.status_code != 200:
            return None, None, "Failed to inspect token"
        insp_data = insp_resp.json()
        open_id = insp_data.get('open_id')
        if not open_id:
            return None, None, "open_id not found"
        
        platform_types = [2, 3, 4, 6, 8]
        for pt in platform_types:
            payload = build_major_login(open_id, access_token, pt)
            encrypted_payload = encrypt_aes(payload)
            
            url = "https://loginbp.ggblueshark.com/MajorLogin"
            headers = {
                "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11; ASUS_Z01QD Build/PI)",
                "Content-Type": "application/x-www-form-urlencoded",
                "X-Unity-Version": "2018.4.11f1",
                "ReleaseVersion": "OB52"
            }
            resp = requests.post(url, data=encrypted_payload, headers=headers, verify=False, timeout=10)
            if resp.status_code == 200:
                major_res = MajorLoginRes()
                major_res.ParseFromString(resp.content)
                if major_res.token:
                    return major_res.token, str(major_res.account_uid), None
        return None, None, "MajorLogin failed - Account may be banned or token invalid"
    except Exception as e:
        return None, None, str(e)

# --- TOKEN MANAGEMENT ---

def generate_token(duration_str=None):
    """Generate a random token with expiration"""
    # Generate 32 character random token
    token = ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(32))
    
    # Parse duration
    days = 0
    if duration_str:
        duration_map = {
            '1day': 1, '2day': 2, '3day': 3, '4day': 4, '5day': 5,
            '6day': 6, '7day': 7, '8day': 8, '9day': 9, '10day': 10,
            '30day': 30, '60day': 60, '90day': 90, '365day': 365,
            '1year': 365, '2year': 730
        }
        days = duration_map.get(duration_str, 0)
    
    expiration = None if days == 0 else (datetime.now() + timedelta(days=days)).timestamp()
    
    access_tokens[token] = {
        'token': token,
        'created_at': datetime.now().timestamp(),
        'expires_at': expiration,
        'duration_str': duration_str or 'unlimited'
    }
    
    save_access_tokens()
    return token, days

def save_access_tokens():
    """Save access tokens to file"""
    try:
        with open(ACCESS_FILE, 'w') as f:
            json.dump(access_tokens, f, indent=2)
        return True
    except Exception as e:
        print(f"[TOKEN SAVE] Error: {e}")
        return False

def load_access_tokens():
    """Load access tokens from file"""
    global access_tokens
    try:
        if os.path.exists(ACCESS_FILE):
            with open(ACCESS_FILE, 'r') as f:
                data = json.load(f)
                access_tokens = data
                # Clean expired tokens
                now = datetime.now().timestamp()
                expired = []
                for token, info in access_tokens.items():
                    if info.get('expires_at') and info['expires_at'] < now:
                        expired.append(token)
                for token in expired:
                    del access_tokens[token]
                if expired:
                    save_access_tokens()
                print(f"[TOKEN LOAD] Loaded {len(access_tokens)} tokens")
        else:
            access_tokens = {}
            save_access_tokens()
    except Exception as e:
        print(f"[TOKEN LOAD] Error: {e}")
        access_tokens = {}

def verify_token(token):
    """Verify if token is valid and not expired"""
    if token not in access_tokens:
        return False, None
    
    info = access_tokens[token]
    if info.get('expires_at'):
        if datetime.now().timestamp() > info['expires_at']:
            del access_tokens[token]
            save_access_tokens()
            return False, None
    
    return True, info

def get_all_tokens():
    """Get all tokens for display"""
    tokens_info = {}
    for token, info in access_tokens.items():
        tokens_info[token] = {
            'created': datetime.fromtimestamp(info['created_at']).strftime('%Y-%m-%d %H:%M:%S'),
            'expires': 'Unlimited' if not info['expires_at'] else datetime.fromtimestamp(info['expires_at']).strftime('%Y-%m-%d %H:%M:%S'),
            'duration': info['duration_str']
        }
    return tokens_info

# --- UTILS ---

def load_uid_jwt_mapping() -> dict:
    global uid_jwt_cache
    try:
        if os.path.exists(UID_FILE):
            with open(UID_FILE, "r", encoding="utf-8") as file:
                content = file.read()
                if content.strip():
                    data = json.loads(content)
                    if isinstance(data, dict):
                        uid_jwt_cache = data
                        print(f"[LOAD] Loaded {len(uid_jwt_cache)} users")
                        return uid_jwt_cache
        else:
            with open(UID_FILE, "w", encoding="utf-8") as file:
                json.dump({}, file)
            uid_jwt_cache = {}
            return {}
    except Exception as e:
        print(f"[LOAD] Error: {e}")
        uid_jwt_cache = {}
        return {}

def save_uid_jwt_mapping():
    global uid_jwt_cache
    try:
        with open(UID_FILE, "w", encoding="utf-8") as file:
            json.dump(uid_jwt_cache, file, indent=2)
        return True
    except Exception as e:
        print(f"[SAVE] Error: {e}")
        return False

def get_jwt_for_uid(uid: str) -> str:
    if not uid_jwt_cache:
        load_uid_jwt_mapping()
    return uid_jwt_cache.get(uid, None)

def checkUIDExists(uid: str) -> bool:
    if not uid_jwt_cache:
        load_uid_jwt_mapping()
    return uid in uid_jwt_cache

def extract_uid_from_login_response(data: bytes) -> str:
    try:
        if len(data) < 2:
            return None
        if data[0] == 0x08:
            uid = 0
            shift = 0
            pos = 1
            while pos < len(data):
                byte = data[pos]
                uid |= (byte & 0x7F) << shift
                shift += 7
                pos += 1
                if not (byte & 0x80):
                    break
            return str(uid)
        for i in range(len(data) - 1):
            if data[i] == 0x08:
                uid = 0
                shift = 0
                pos = i + 1
                while pos < len(data):
                    byte = data[pos]
                    uid |= (byte & 0x7F) << shift
                    shift += 7
                    pos += 1
                    if not (byte & 0x80):
                        break
                return str(uid)
        return None
    except Exception as e:
        print(f"[UID] Error extracting UID: {e}")
        return None

def modify_get_account_response(data: bytes, nickname: str, reason: str) -> bytes:
    try:
        fields = {}
        pos = 0
        data_len = len(data)
        
        while pos < data_len:
            if pos >= data_len:
                break
            tag = data[pos]
            field_num = tag >> 3
            wire_type = tag & 0x07
            pos += 1
            
            if wire_type == 0:
                value = 0
                shift = 0
                while pos < data_len:
                    byte = data[pos]
                    value |= (byte & 0x7F) << shift
                    pos += 1
                    shift += 7
                    if not (byte & 0x80):
                        break
                fields[field_num] = ('varint', value)
            elif wire_type == 2:
                length = 0
                shift = 0
                while pos < data_len:
                    byte = data[pos]
                    length |= (byte & 0x7F) << shift
                    pos += 1
                    shift += 7
                    if not (byte & 0x80):
                        break
                if pos + length <= data_len:
                    value = data[pos:pos + length]
                    pos += length
                    fields[field_num] = ('string', value)
        
        result = bytearray()
        
        if 1 in fields:
            result.append(0x08)
            account_id = fields[1][1]
            while account_id > 0x7F:
                result.append((account_id & 0x7F) | 0x80)
                account_id >>= 7
            result.append(account_id & 0x7F)
        
        new_nickname = f"[c][ff0000]{nickname}\n[000000]Reason:[b][c][ff0000]{reason}"
        nickname_bytes = new_nickname.encode('utf-8')
        result.append(0x12)
        length = len(nickname_bytes)
        while length > 0x7F:
            result.append((length & 0x7F) | 0x80)
            length >>= 7
        result.append(length & 0x7F)
        result.extend(nickname_bytes)
        
        if 3 in fields:
            result.append(0x18)
            field3 = fields[3][1]
            while field3 > 0x7F:
                result.append((field3 & 0x7F) | 0x80)
                field3 >>= 7
            result.append(field3 & 0x7F)
        
        if 5 in fields:
            result.append(0x28)
            field5 = fields[5][1]
            while field5 > 0x7F:
                result.append((field5 & 0x7F) | 0x80)
                field5 >>= 7
            result.append(field5 & 0x7F)
        
        if 6 in fields:
            result.append(0x32)
            region_bytes = fields[6][1]
            length = len(region_bytes)
            while length > 0x7F:
                result.append((length & 0x7F) | 0x80)
                length >>= 7
            result.append(length & 0x7F)
            result.extend(region_bytes)
        
        return bytes(result)
    except Exception as e:
        print(f"[Modify] Error modifying response: {e}")
        return data

# --- HTML CONTENT ---

def get_html_content(template_name):
    """Read HTML template from file"""
    template_path = TEMPLATES_DIR / template_name
    if template_path.exists():
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    return None

def get_css_content():
    """Read CSS from file"""
    css_path = STATIC_DIR / "css" / "style.css"
    if css_path.exists():
        with open(css_path, 'r', encoding='utf-8') as f:
            return f.read()
    return None

def get_js_content():
    """Read JS from file"""
    js_path = STATIC_DIR / "js" / "main.js"
    if js_path.exists():
        with open(js_path, 'r', encoding='utf-8') as f:
            return f.read()
    return None

LOGIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Login - UID Manager</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{background:linear-gradient(135deg,#0a0a0f 0%,#0d1b2a 50%,#0a0a0f 100%);min-height:100vh;display:flex;align-items:center;justify-content:center;font-family:'Segoe UI',sans-serif;}
.card{background:rgba(13,27,42,0.95);border:1px solid rgba(0,255,136,0.15);border-radius:20px;padding:40px 36px;width:360px;box-shadow:0 20px 60px rgba(0,0,0,0.6);}
.logo{text-align:center;margin-bottom:30px;}
.logo h1{color:#00ff88;font-size:26px;font-weight:800;letter-spacing:1px;}
.logo p{color:#556;font-size:13px;margin-top:6px;}
.field{margin-bottom:18px;}
.field label{display:block;color:#8899aa;font-size:12px;font-weight:600;margin-bottom:7px;text-transform:uppercase;letter-spacing:.5px;}
.field input{width:100%;background:#0b1422;border:1px solid #1e2d40;color:#fff;padding:13px 16px;border-radius:10px;font-size:14px;outline:none;transition:border .2s;}
.field input:focus{border-color:#00ff88;}
.btn{width:100%;background:linear-gradient(135deg,#00ff88,#00c4ff);border:none;color:#000;font-weight:700;font-size:16px;padding:15px;border-radius:12px;cursor:pointer;margin-top:8px;transition:opacity .2s;}
.btn:hover{opacity:.9;}
.btn:disabled{opacity:.5;cursor:not-allowed;}
.err{background:rgba(255,60,60,.1);border:1px solid rgba(255,60,60,.3);color:#ff6060;padding:12px 16px;border-radius:10px;font-size:13px;margin-top:14px;display:none;}
.err.show{display:block;}
.spin{display:inline-block;width:16px;height:16px;border:2px solid rgba(0,0,0,.2);border-top-color:#000;border-radius:50%;animation:spin .7s linear infinite;vertical-align:middle;margin-right:6px;}
@keyframes spin{to{transform:rotate(360deg);}}
</style>
</head>
<body>
<div class="card">
  <div class="logo">
    <h1>&#128274; UID Manager</h1>
    <p>Enter your token and password to continue</p>
  </div>
  <div class="field">
    <label>Access Token</label>
    <input type="text" id="token" placeholder="Paste your token here..." autocomplete="off"/>
  </div>
  <div class="field">
    <label>Password</label>
    <input type="password" id="password" placeholder="Enter password"/>
  </div>
  <button class="btn" id="loginBtn" onclick="doLogin()">Login</button>
  <div class="err" id="errBox"></div>
</div>
<script>
document.getElementById('password').addEventListener('keydown',function(e){if(e.key==='Enter')doLogin();});
document.getElementById('token').addEventListener('keydown',function(e){if(e.key==='Enter')doLogin();});
async function doLogin(){
  const btn=document.getElementById('loginBtn');
  const errBox=document.getElementById('errBox');
  const token=document.getElementById('token').value.trim();
  const password=document.getElementById('password').value.trim();
  if(!token||!password){errBox.textContent='Please enter token and password.';errBox.className='err show';return;}
  btn.disabled=true;
  btn.innerHTML='<span class=\"spin\"></span>Logging in...';
  errBox.className='err';
  try{
    const res=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token,password})});
    const data=await res.json();
    if(data.success){
      document.cookie='auth_token='+data.token+';path=/;samesite=lax';
      window.location.href='/dashboard';
    }else{
      errBox.textContent=data.error||'Login failed.';
      errBox.className='err show';
    }
  }catch(e){
    errBox.textContent='Network error: '+e.message;
    errBox.className='err show';
  }finally{
    btn.disabled=false;
    btn.innerHTML='Login';
  }
}
</script>
</body>
</html>
"""

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Dashboard - UID Manager</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{background:#080d16;color:#cdd;font-family:'Segoe UI',sans-serif;min-height:100vh;}
header{background:rgba(13,27,42,.98);border-bottom:1px solid rgba(0,255,136,.12);padding:14px 24px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:100;}
header h1{color:#00ff88;font-size:20px;font-weight:800;}
header .meta{display:flex;align-items:center;gap:16px;}
.timer-badge{background:rgba(0,255,136,.1);border:1px solid rgba(0,255,136,.3);color:#00ff88;padding:6px 14px;border-radius:20px;font-size:13px;font-weight:600;}
.logout-btn{background:rgba(255,60,60,.1);border:1px solid rgba(255,60,60,.3);color:#ff6060;padding:6px 14px;border-radius:8px;cursor:pointer;font-size:13px;}
.logout-btn:hover{background:rgba(255,60,60,.2);}
.main{padding:24px;max-width:1000px;margin:0 auto;}
.info-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:14px;margin-bottom:24px;}
.info-card{background:rgba(13,27,42,.9);border:1px solid #1e3050;border-radius:14px;padding:18px;}
.info-card .ic-label{color:#5566aa;font-size:11px;text-transform:uppercase;letter-spacing:.6px;margin-bottom:6px;}
.info-card .ic-val{color:#eef;font-size:14px;font-weight:600;word-break:break-all;}
.section{background:rgba(13,27,42,.9);border:1px solid #1e3050;border-radius:16px;padding:22px;margin-bottom:20px;}
.section h2{color:#00ff88;font-size:16px;font-weight:700;margin-bottom:16px;display:flex;align-items:center;gap:8px;}
.input-row{display:flex;gap:10px;margin-bottom:14px;flex-wrap:wrap;}
.input-row input,.input-row select{flex:1;min-width:140px;background:#0b1422;border:1px solid #1e2d40;color:#fff;padding:11px 14px;border-radius:10px;font-size:13px;outline:none;}
.input-row input:focus,.input-row select:focus{border-color:#00ff88;}
.btn-primary{background:linear-gradient(135deg,#00ff88,#00c4ff);border:none;color:#000;font-weight:700;padding:11px 22px;border-radius:10px;cursor:pointer;font-size:13px;white-space:nowrap;}
.btn-primary:hover{opacity:.88;}
.btn-danger{background:rgba(255,60,60,.15);border:1px solid rgba(255,60,60,.4);color:#ff6060;padding:8px 16px;border-radius:8px;cursor:pointer;font-size:12px;}
.btn-danger:hover{background:rgba(255,60,60,.25);}
.result-box{background:#060b12;border:1px solid rgba(0,255,136,.2);border-radius:10px;padding:14px;font-family:monospace;font-size:12px;color:#00ff88;word-break:break-all;margin-top:12px;display:none;max-height:180px;overflow-y:auto;}
.result-box.show{display:block;}
table{width:100%;border-collapse:collapse;font-size:13px;}
table th{color:#5566aa;text-align:left;padding:10px 12px;border-bottom:1px solid #1e3050;font-size:11px;text-transform:uppercase;letter-spacing:.5px;}
table td{padding:10px 12px;border-bottom:1px solid #0d1a2a;color:#ccd;vertical-align:middle;}
table tr:hover td{background:rgba(0,255,136,.03);}
.uid-cell{font-family:monospace;font-size:12px;color:#88aaff;}
.jwt-cell{font-family:monospace;font-size:11px;color:#556;max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.empty-state{text-align:center;color:#334;padding:40px;font-size:14px;}
.token-gen-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(90px,1fr));gap:10px;margin-bottom:16px;}
.dur-btn{background:rgba(255,255,255,.04);border:1px solid #1e2d40;color:#aabbcc;padding:10px;border-radius:10px;cursor:pointer;font-size:13px;text-align:center;}
.dur-btn:hover,.dur-btn.active{background:rgba(0,255,136,.12);border-color:#00ff88;color:#00ff88;}
.gen-token-display{background:#060b12;border:1px solid rgba(0,255,136,.3);border-radius:10px;padding:14px;font-family:monospace;font-size:13px;color:#00ff88;word-break:break-all;margin-top:12px;display:none;}
.gen-token-display.show{display:block;}
.copy-btn{background:rgba(0,255,136,.15);border:1px solid rgba(0,255,136,.4);color:#00ff88;padding:8px 16px;border-radius:8px;cursor:pointer;font-size:12px;margin-top:8px;width:100%;}
.toast{position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:#00ff88;color:#000;padding:12px 24px;border-radius:30px;font-weight:700;font-size:13px;display:none;z-index:999;box-shadow:0 4px 20px rgba(0,255,136,.3);}
.spin{display:inline-block;width:14px;height:14px;border:2px solid rgba(0,0,0,.15);border-top-color:#000;border-radius:50%;animation:spin .7s linear infinite;vertical-align:middle;}
@keyframes spin{to{transform:rotate(360deg);}}
</style>
</head>
<body>
<header>
  <h1>&#9881; UID/JWT Manager</h1>
  <div class="meta">
    <div class="timer-badge">&#9201; <span id="timerDisplay">{{REMAINING_TIME}}</span></div>
    <button class="logout-btn" onclick="logout()">Logout</button>
  </div>
</header>

<div class="main">

  <!-- Info Cards -->
  <div class="info-grid">
    <div class="info-card">
      <div class="ic-label">OID</div>
      <div class="ic-val" style="font-size:11px;color:#8899bb;">{{OID}}</div>
    </div>
    <div class="info-card">
      <div class="ic-label">Bound Platform</div>
      <div class="ic-val">Google</div>
    </div>
    <div class="info-card">
      <div class="ic-label">Recent Access</div>
      <div class="ic-val" style="color:#ffcc00;">{{BROWSER}}</div>
    </div>
    <div class="info-card">
      <div class="ic-label">Status</div>
      <div class="ic-val" style="color:#00ff88;">&#9679; Active</div>
    </div>
  </div>

  <!-- Token Generator -->
  <div class="section">
    <h2>&#128273; Generate Token</h2>
    <div class="token-gen-grid">
      <div class="dur-btn active" data-dur="">Unlimited</div>
      <div class="dur-btn" data-dur="1day">1 Day</div>
      <div class="dur-btn" data-dur="7day">7 Days</div>
      <div class="dur-btn" data-dur="30day">30 Days</div>
      <div class="dur-btn" data-dur="90day">90 Days</div>
      <div class="dur-btn" data-dur="1year">1 Year</div>
    </div>
    <button class="btn-primary" id="genTokenBtn" onclick="generateToken()">&#10024; Generate Token</button>
    <div class="gen-token-display" id="genTokenBox"></div>
    <button class="copy-btn" id="copyGenBtn" style="display:none;" onclick="copyGenToken()">&#128203; Copy Token</button>
  </div>

  <!-- Convert Access Token -->
  <div class="section">
    <h2>&#128260; Convert Access Token &#8594; JWT</h2>
    <div class="input-row">
      <input type="text" id="accessTokenInput" placeholder="Paste Garena access_token here..."/>
      <button class="btn-primary" onclick="convertToken()">Convert</button>
    </div>
    <div class="result-box" id="convertResult"></div>
  </div>

  <!-- Decode JWT -->
  <div class="section">
    <h2>&#128065; Decode JWT</h2>
    <div class="input-row">
      <input type="text" id="jwtDecodeInput" placeholder="Paste JWT token here..."/>
      <button class="btn-primary" onclick="decodeJWT()">Decode</button>
    </div>
    <div class="result-box" id="decodeResult"></div>
  </div>

  <!-- Add User -->
  <div class="section">
    <h2>&#10133; Add User (UID + JWT)</h2>
    <div class="input-row">
      <input type="text" id="addUid" placeholder="UID"/>
      <input type="text" id="addJwt" placeholder="JWT Token"/>
      <button class="btn-primary" onclick="addUser()">Add</button>
    </div>
    <div class="result-box" id="addResult"></div>
  </div>

  <!-- Users List -->
  <div class="section">
    <h2>&#128101; Registered Users</h2>
    <div id="usersTable"><div class="empty-state">Loading...</div></div>
  </div>

</div>

<div class="toast" id="toast"></div>

<script>
const TOKEN = '{{TOKEN}}';

function getCookie(name){
  const v=document.cookie.match('(^|;) ?'+name+'=([^;]*)(;|$)');
  return v?v[2]:null;
}
function authHeaders(){return{'Content-Type':'application/json','Authorization':'Bearer '+TOKEN};}

function logout(){
  document.cookie='auth_token=;path=/;expires=Thu, 01 Jan 1970 00:00:00 GMT';
  window.location.href='/login';
}

function toast(msg,err=false){
  const t=document.getElementById('toast');
  t.textContent=msg;t.style.background=err?'#ff4444':'#00ff88';t.style.color=err?'#fff':'#000';
  t.style.display='block';setTimeout(()=>t.style.display='none',3000);
}

// ── Token Timer ──
(function(){
  const rt='{{REMAINING_TIME}}';
  if(rt==='Unlimited'||rt==='Expired'){return;}
  // parse remaining
  function parseRemaining(s){
    let total=0;
    const dm=s.match(/(\d+)d/);const hm=s.match(/(\d+)h/);const mm=s.match(/(\d+)m/);const sm=s.match(/(\d+)s/);
    if(dm)total+=parseInt(dm[1])*86400;if(hm)total+=parseInt(hm[1])*3600;if(mm)total+=parseInt(mm[1])*60;if(sm)total+=parseInt(sm[1]);
    return total;
  }
  let secs=parseRemaining(rt);
  function fmt(s){
    const d=Math.floor(s/86400);const h=Math.floor((s%86400)/3600);const m=Math.floor((s%3600)/60);const sc=s%60;
    if(d>0)return d+'d '+h+'h '+m+'m '+sc+'s';if(h>0)return h+'h '+m+'m '+sc+'s';return m+'m '+sc+'s';
  }
  setInterval(()=>{
    if(secs>0){secs--;document.getElementById('timerDisplay').textContent=fmt(secs);}
    else{document.getElementById('timerDisplay').textContent='Expired';}
  },1000);
})();

// ── Token Generator ──
let selDur='';
document.querySelectorAll('.dur-btn').forEach(b=>{
  b.addEventListener('click',function(){
    document.querySelectorAll('.dur-btn').forEach(x=>x.classList.remove('active'));
    this.classList.add('active');selDur=this.dataset.dur;
  });
});

async function generateToken(){
  const btn=document.getElementById('genTokenBtn');
  btn.disabled=true;btn.innerHTML='<span class="spin"></span> Generating...';
  try{
    let url='/api/generate_token';
    if(selDur)url+='?duration='+selDur;
    const r=await fetch(url,{headers:authHeaders()});
    const d=await r.json();
    if(d.success){
      const box=document.getElementById('genTokenBox');
      box.textContent='Token: '+d.token+'\nDuration: '+(d.duration||'Unlimited');
      box.className='gen-token-display show';
      document.getElementById('copyGenBtn').style.display='block';
      toast('Token generated!');
    }else{toast(d.error||'Failed',true);}
  }catch(e){toast('Error: '+e.message,true);}
  finally{btn.disabled=false;btn.innerHTML='&#10024; Generate Token';}
}

function copyGenToken(){
  const box=document.getElementById('genTokenBox');
  const lines=box.textContent.split('\n');
  const token=lines[0].replace('Token: ','').trim();
  navigator.clipboard.writeText(token).then(()=>toast('Copied!'));
}

// ── Convert Token ──
async function convertToken(){
  const at=document.getElementById('accessTokenInput').value.trim();
  if(!at){toast('Enter access token',true);return;}
  const res=document.getElementById('convertResult');
  res.textContent='Converting...';res.className='result-box show';
  try{
    const r=await fetch('/api/convert',{method:'POST',headers:authHeaders(),body:JSON.stringify({access_token:at})});
    const d=await r.json();
    res.textContent=JSON.stringify(d,null,2);
    if(d.success){toast('Converted! UID: '+d.uid);loadUsers();}
    else toast(d.error||'Failed',true);
  }catch(e){res.textContent='Error: '+e.message;toast('Error',true);}
}

// ── Decode JWT ──
async function decodeJWT(){
  const jt=document.getElementById('jwtDecodeInput').value.trim();
  if(!jt){toast('Enter JWT',true);return;}
  const res=document.getElementById('decodeResult');
  res.textContent='Decoding...';res.className='result-box show';
  try{
    const r=await fetch('/api/decode',{method:'POST',headers:authHeaders(),body:JSON.stringify({token:jt})});
    const d=await r.json();
    res.textContent=JSON.stringify(d,null,2);
  }catch(e){res.textContent='Error: '+e.message;}
}

// ── Add User ──
async function addUser(){
  const uid=document.getElementById('addUid').value.trim();
  const jwt=document.getElementById('addJwt').value.trim();
  if(!uid||!jwt){toast('UID and JWT required',true);return;}
  const res=document.getElementById('addResult');
  try{
    const r=await fetch('/api/users',{method:'POST',headers:authHeaders(),body:JSON.stringify({uid,jwt})});
    const d=await r.json();
    res.textContent=JSON.stringify(d,null,2);res.className='result-box show';
    if(d.success){toast('User added!');loadUsers();document.getElementById('addUid').value='';document.getElementById('addJwt').value='';}
    else toast(d.error||'Failed',true);
  }catch(e){res.textContent='Error: '+e.message;res.className='result-box show';}
}

// ── Delete User ──
async function deleteUser(uid){
  if(!confirm('Delete UID '+uid+'?'))return;
  try{
    const r=await fetch('/api/users/'+uid,{method:'DELETE',headers:authHeaders()});
    const d=await r.json();
    if(d.success){toast('Deleted!');loadUsers();}
    else toast(d.error||'Failed',true);
  }catch(e){toast('Error',true);}
}

// ── Load Users ──
async function loadUsers(){
  const el=document.getElementById('usersTable');
  try{
    const r=await fetch('/api/users',{headers:authHeaders()});
    const d=await r.json();
    const keys=Object.keys(d);
    if(keys.length===0){el.innerHTML='<div class=\"empty-state\">No users registered yet.</div>';return;}
    let html='<table><thead><tr><th>#</th><th>UID</th><th>JWT (preview)</th><th>Action</th></tr></thead><tbody>';
    keys.forEach((uid,i)=>{
      const jwt=d[uid];
      const preview=jwt.length>40?jwt.substring(0,40)+'...':jwt;
      html+=`<tr><td>${i+1}</td><td class="uid-cell">${uid}</td><td class="jwt-cell" title="${jwt}">${preview}</td><td><button class="btn-danger" onclick="deleteUser('${uid}')">Delete</button></td></tr>`;
    });
    html+='</tbody></table>';
    el.innerHTML=html;
  }catch(e){el.innerHTML='<div class=\"empty-state\">Error loading users.</div>';}
}

loadUsers();
</script>
</body>
</html>
"""

# --- TOKEN GENERATION HTML PAGE ---

TOKEN_GEN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Token Generator</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container { max-width: 600px; width: 100%; }
        .card {
            background: rgba(26, 26, 46, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 30px;
            padding: 40px;
            border: 1px solid rgba(0, 255, 136, 0.2);
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        }
        h1 {
            color: #00ff88;
            font-size: 28px;
            margin-bottom: 10px;
            text-align: center;
        }
        .subtitle {
            color: #888;
            text-align: center;
            margin-bottom: 30px;
            font-size: 14px;
        }
        .duration-buttons {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
            gap: 12px;
            margin-bottom: 30px;
        }
        .dur-btn {
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            color: white;
            padding: 12px;
            border-radius: 15px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s ease;
        }
        .dur-btn:hover {
            background: rgba(0, 255, 136, 0.1);
            border-color: #00ff88;
            transform: translateY(-2px);
        }
        .dur-btn.active {
            background: linear-gradient(135deg, #00ff88, #00b4d8);
            color: #000;
            border-color: transparent;
        }
        .generate-btn {
            background: linear-gradient(135deg, #00ff88, #00b4d8);
            border: none;
            color: #000;
            font-weight: bold;
            padding: 16px;
            border-radius: 50px;
            cursor: pointer;
            font-size: 18px;
            width: 100%;
            margin-bottom: 20px;
            transition: all 0.3s ease;
        }
        .generate-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(0, 255, 136, 0.3);
        }
        .result {
            background: rgba(0, 0, 0, 0.5);
            border-radius: 20px;
            padding: 20px;
            margin-top: 20px;
            display: none;
            border: 1px solid rgba(0, 255, 136, 0.3);
        }
        .result.show { display: block; animation: fadeIn 0.5s ease; }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .token-display {
            background: #0a0a0a;
            padding: 15px;
            border-radius: 15px;
            font-family: monospace;
            font-size: 14px;
            word-break: break-all;
            color: #00ff88;
            margin: 15px 0;
            border: 1px solid rgba(0, 255, 136, 0.3);
        }
        .copy-btn {
            background: rgba(0, 255, 136, 0.2);
            border: 1px solid #00ff88;
            color: #00ff88;
            padding: 10px 20px;
            border-radius: 10px;
            cursor: pointer;
            width: 100%;
            font-weight: bold;
        }
        .info {
            color: #666;
            font-size: 12px;
            text-align: center;
            margin-top: 20px;
        }
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid rgba(0,0,0,0.1);
            border-top-color: #000;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        .toast {
            position: fixed;
            bottom: 20px;
            left: 20px;
            right: 20px;
            background: #00ff88;
            color: #000;
            padding: 15px;
            border-radius: 15px;
            text-align: center;
            font-weight: bold;
            display: none;
            z-index: 1000;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h1>🔑 Token Generator</h1>
            <div class="subtitle">Generate access tokens for authentication</div>
            
            <div class="duration-buttons">
                <button class="dur-btn" data-duration="">Unlimited</button>
                <button class="dur-btn" data-duration="1day">1 Day</button>
                <button class="dur-btn" data-duration="7day">7 Days</button>
                <button class="dur-btn" data-duration="30day">30 Days</button>
                <button class="dur-btn" data-duration="1year">1 Year</button>
            </div>
            
            <button class="generate-btn" id="generateBtn">✨ Generate Token</button>
            
            <div id="result" class="result">
                <div style="color: #00ff88; margin-bottom: 10px;">✅ Token Generated Successfully!</div>
                <div class="token-display" id="tokenValue"></div>
                <div style="color: #aaa; font-size: 12px; margin-bottom: 10px;">
                    Duration: <span id="durationDisplay"></span><br>
                    Password: <strong>test</strong>
                </div>
                <button class="copy-btn" id="copyBtn">📋 Copy Token</button>
                <div class="info">
                    Use this token to login at: <strong>/login</strong><br>
                    Default password: <strong>test</strong>
                </div>
            </div>
        </div>
    </div>
    
    <div id="toast" class="toast"></div>
    
    <script>
        let selectedDuration = '';
        
        document.querySelectorAll('.dur-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                document.querySelectorAll('.dur-btn').forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                selectedDuration = this.dataset.duration;
            });
        });
        
        document.getElementById('generateBtn').addEventListener('click', async function() {
            const btn = this;
            const originalText = btn.innerHTML;
            btn.innerHTML = '<span class="loading"></span> Generating...';
            btn.disabled = true;
            
            try {
                let url = '/api/generate_token';
                if (selectedDuration) {
                    url += `?duration=${selectedDuration}`;
                }
                
                const response = await fetch(url);
                const data = await response.json();
                
                if (data.success) {
                    document.getElementById('tokenValue').textContent = data.token;
                    document.getElementById('durationDisplay').textContent = data.duration || 'Unlimited';
                    document.getElementById('result').classList.add('show');
                    showToast('Token generated successfully!');
                } else {
                    showToast('Failed to generate token: ' + data.error, true);
                }
            } catch (error) {
                showToast('Error: ' + error.message, true);
            } finally {
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        });
        
        document.getElementById('copyBtn').addEventListener('click', function() {
            const token = document.getElementById('tokenValue').textContent;
            navigator.clipboard.writeText(token);
            showToast('Token copied to clipboard!');
        });
        
        function showToast(message, isError = false) {
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.style.background = isError ? '#ff4444' : '#00ff88';
            toast.style.color = isError ? 'white' : 'black';
            toast.style.display = 'block';
            setTimeout(() => {
                toast.style.display = 'none';
            }, 3000);
        }
        
        // Select unlimited by default
        document.querySelector('.dur-btn[data-duration=""]').classList.add('active');
    </script>
</body>
</html>
"""

# --- MITMPROXY ADDON ---

class UIDJWTManager:
    def __init__(self):
        self.valid_uid_detected = False
        self.current_uid = None
        self.current_jwt = None
        self.session_tokens = {}
        print("\n[INIT] UID/JWT Manager initialized on port 20335")
        load_uid_jwt_mapping()
        load_access_tokens()
    
    def request(self, flow: http.HTTPFlow) -> None:
        path = flow.request.path
        method = flow.request.method
        
        print(f"[DEBUG] {method} {path}")
        
        # ============ TOKEN GENERATION API ============
        if path == "/api/generate_token":
            query = flow.request.query
            duration = query.get('duration', [''])[0] if query.get('duration') else ''
            if duration == '':
                duration = None
            
            token, days = generate_token(duration)
            duration_str = 'Unlimited' if days == 0 else f'{days} Days'
            
            flow.response = http.Response.make(200, json.dumps({
                'success': True,
                'token': token,
                'duration': duration_str,
                'days': days
            }).encode(), {"Content-Type": "application/json"})
            return
        
        # ============ TOKEN GENERATOR PAGE ============
        if path == "/token" or path == "/token.html" or path == "/generator":
            flow.response = http.Response.make(200, TOKEN_GEN_HTML.encode(), {"Content-Type": "text/html"})
            return
        
        # ============ SIMPLE TOKEN GENERATION (GET) ============
        if path.startswith("/generate"):
            duration = None
            raw_qs = ""
            if '?' in path:
                raw_qs = path.split('?', 1)[1]
            # Support ?duration=1day OR ?1day OR ?30day OR ?unlimited
            if '=' in raw_qs:
                key, val = raw_qs.split('=', 1)
                if key == 'duration' and val:
                    duration = val
            elif raw_qs and raw_qs not in ('unlimited', ''):
                duration = raw_qs  # e.g. ?1day ?30day
            
            token, days = generate_token(duration)
            response_text = f"""
╔══════════════════════════════════════════════════════════════════╗
║                      TOKEN GENERATED                             ║
╠══════════════════════════════════════════════════════════════════╣
║  Token: {token}
║  Duration: {'Unlimited' if days == 0 else f'{days} Days'}
║  Password: test
║
║  Login URL: http://{flow.request.host}/login
║  Dashboard: http://{flow.request.host}/dashboard
╚══════════════════════════════════════════════════════════════════╝
"""
            flow.response = http.Response.make(200, response_text.encode(), {"Content-Type": "text/plain"})
            return
        
        # ============ TOKEN LIST ============
        if path == "/tokens" or path == "/api/tokens":
            tokens_info = get_all_tokens()
            flow.response = http.Response.make(200, json.dumps(tokens_info, indent=2).encode(), {"Content-Type": "application/json"})
            return
        
        # ============ STATIC FILES ============
        if path.startswith("/static/"):
            if path.endswith(".css"):
                css_content = get_css_content()
                if css_content:
                    flow.response = http.Response.make(200, css_content.encode(), {"Content-Type": "text/css"})
                    return
            elif path.endswith(".js"):
                js_content = get_js_content()
                if js_content:
                    flow.response = http.Response.make(200, js_content.encode(), {"Content-Type": "application/javascript"})
                    return
            flow.response = http.Response.make(404, b"Not found", {"Content-Type": "text/plain"})
            return
        
        # ============ CERTIFICATE ============
        if path == "/certificate":
            cert_path = Path(CERT_FILE)
            if cert_path.exists():
                with open(cert_path, "rb") as f:
                    cert_data = f.read()
                flow.response = http.Response.make(200, cert_data, {
                    "Content-Type": "application/x-pem-file",
                    "Content-Disposition": "attachment; filename=mitmproxy-ca-cert.pem"
                })
                return
            else:
                flow.response = http.Response.make(404, b"Certificate not found", {"Content-Type": "text/plain"})
                return
        
        # ============ MAIN PAGE ============
        if path == "/" or path == "/main":
            html = get_html_content('main.html')
            if html:
                flow.response = http.Response.make(200, html.encode(), {"Content-Type": "text/html"})
            else:
                flow.response = http.Response.make(404, b"Template not found", {"Content-Type": "text/plain"})
            return
        
        # ============ LOGIN PAGE ============
        if path == "/login":
            html = get_html_content('login.html') or LOGIN_HTML
            flow.response = http.Response.make(200, html.encode(), {"Content-Type": "text/html"})
            return
        
        # ============ DASHBOARD PAGE ============
        if path == "/dashboard":
            auth_token = None
            # Check cookie first (browser navigation)
            cookie_header = flow.request.headers.get('Cookie', '')
            for part in cookie_header.split(';'):
                part = part.strip()
                if part.startswith('auth_token='):
                    auth_token = part[len('auth_token='):]
                    break
            # Fallback: Authorization header (API calls)
            if not auth_token:
                if 'Authorization' in flow.request.headers:
                    auth_header = flow.request.headers['Authorization']
                    if auth_header.startswith('Bearer '):
                        auth_token = auth_header[7:]
            
            if not auth_token:
                flow.response = http.Response.make(302, b"", {"Location": "/login"})
                return
            
            valid, info = verify_token(auth_token)
            if not valid:
                flow.response = http.Response.make(302, b"", {"Location": "/login"})
                return
            
            html = get_html_content('dashboard.html')
            if html:
                remaining_time = "Unlimited"
                if info.get('expires_at'):
                    remaining_seconds = int(info['expires_at'] - datetime.now().timestamp())
                    if remaining_seconds > 0:
                        days = remaining_seconds // 86400
                        hours = (remaining_seconds % 86400) // 3600
                        minutes = (remaining_seconds % 3600) // 60
                        seconds = remaining_seconds % 60
                        if days > 0:
                            remaining_time = f"{days}d {hours}h {minutes}m {seconds}s"
                        elif hours > 0:
                            remaining_time = f"{hours}h {minutes}m {seconds}s"
                        else:
                            remaining_time = f"{minutes}m {seconds}s"
                    else:
                        remaining_time = "Expired"
                
                html = html.replace('{{REMAINING_TIME}}', remaining_time)
                html = html.replace('{{TOKEN}}', auth_token)
                
                import random
                oid = ''.join(random.choices('0123456789abcdef', k=32))
                html = html.replace('{{OID}}', oid)
                
                user_agent = flow.request.headers.get('User-Agent', 'Unknown')
                browser = "Unknown"
                if 'Chrome' in user_agent:
                    browser = "Chrome"
                elif 'Firefox' in user_agent:
                    browser = "Firefox"
                elif 'Safari' in user_agent:
                    browser = "Safari"
                elif 'Edge' in user_agent:
                    browser = "Edge"
                html = html.replace('{{BROWSER}}', browser)
                
                flow.response = http.Response.make(200, html.encode(), {"Content-Type": "text/html"})
            else:
                html = DASHBOARD_HTML
                remaining_time = "Unlimited"
                if info.get('expires_at'):
                    remaining_seconds = int(info['expires_at'] - datetime.now().timestamp())
                    if remaining_seconds > 0:
                        days_r = remaining_seconds // 86400
                        hours_r = (remaining_seconds % 86400) // 3600
                        minutes_r = (remaining_seconds % 3600) // 60
                        seconds_r = remaining_seconds % 60
                        if days_r > 0:
                            remaining_time = f"{days_r}d {hours_r}h {minutes_r}m {seconds_r}s"
                        elif hours_r > 0:
                            remaining_time = f"{hours_r}h {minutes_r}m {seconds_r}s"
                        else:
                            remaining_time = f"{minutes_r}m {seconds_r}s"
                    else:
                        remaining_time = "Expired"
                import random
                oid = ''.join(random.choices('0123456789abcdef', k=32))
                user_agent = flow.request.headers.get('User-Agent', 'Unknown')
                browser = "Unknown"
                if 'Chrome' in user_agent: browser = "Chrome"
                elif 'Firefox' in user_agent: browser = "Firefox"
                elif 'Safari' in user_agent: browser = "Safari"
                elif 'Edge' in user_agent: browser = "Edge"
                html = html.replace('{{REMAINING_TIME}}', remaining_time).replace('{{TOKEN}}', auth_token).replace('{{OID}}', oid).replace('{{BROWSER}}', browser)
                flow.response = http.Response.make(200, html.encode(), {"Content-Type": "text/html"})
            return
        
        # ============ API ENDPOINTS ============
        if path.startswith("/api/"):
            self.handle_api(flow)
            return
        
        # ============ JWT REPLACEMENT ============
        if self.valid_uid_detected and self.current_jwt:
            try:
                if "majorlogin" in path.lower():
                    return
                if "Authorization" in flow.request.headers:
                    auth = flow.request.headers["Authorization"]
                    if auth.startswith("Bearer "):
                        print(f"\n[JWT] Replacing token for UID: {self.current_uid}")
                        flow.request.headers["Authorization"] = "Bearer " + self.current_jwt
            except Exception as e:
                print(f"[JWT ERROR] {e}")
    
    def handle_api(self, flow: http.HTTPFlow):
        path = flow.request.path
        method = flow.request.method
        
        flow.response = http.Response.make(200, b"", {"Content-Type": "application/json"})
        
        # Auth check
        auth_token = None
        if 'Authorization' in flow.request.headers:
            auth_header = flow.request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                auth_token = auth_header[7:]
        
        # Login API
        if method == "POST" and path == "/api/login":
            try:
                data = json.loads(flow.request.content.decode())
                token = data.get('token')
                password = data.get('password')
                
                if password != "test":
                    flow.response.content = json.dumps({'success': False, 'error': 'Invalid password'}).encode()
                    return
                
                valid, info = verify_token(token)
                if valid:
                    flow.response.content = json.dumps({'success': True, 'token': token}).encode()
                    flow.response.headers['Set-Cookie'] = f'auth_token={token}; Path=/; HttpOnly; SameSite=Lax'
                else:
                    flow.response.content = json.dumps({'success': False, 'error': 'Invalid or expired token'}).encode()
            except Exception as e:
                flow.response.content = json.dumps({'success': False, 'error': str(e)}).encode()
            return
        
        # GET /api/users
        if method == "GET" and path == "/api/users":
            if not auth_token or not verify_token(auth_token)[0]:
                flow.response.status_code = 401
                flow.response.content = json.dumps({'error': 'Unauthorized'}).encode()
                return
            flow.response.content = json.dumps(uid_jwt_cache).encode()
            return
        
        # POST /api/convert
        if method == "POST" and path == "/api/convert":
            if not auth_token or not verify_token(auth_token)[0]:
                flow.response.status_code = 401
                flow.response.content = json.dumps({'error': 'Unauthorized'}).encode()
                return
            try:
                data = json.loads(flow.request.content.decode())
                access_token = data.get('access_token')
                if not access_token:
                    flow.response.content = json.dumps({'success': False, 'error': 'Access token required'}).encode()
                    return
                jwt, uid, error = access_token_to_jwt(access_token)
                if jwt and uid:
                    uid_jwt_cache[uid] = jwt
                    save_uid_jwt_mapping()
                    flow.response.content = json.dumps({'success': True, 'jwt': jwt, 'uid': uid}).encode()
                else:
                    flow.response.content = json.dumps({'success': False, 'error': error or 'Conversion failed'}).encode()
            except Exception as e:
                flow.response.content = json.dumps({'success': False, 'error': str(e)}).encode()
            return
        
        # POST /api/decode
        if method == "POST" and path == "/api/decode":
            if not auth_token or not verify_token(auth_token)[0]:
                flow.response.status_code = 401
                flow.response.content = json.dumps({'error': 'Unauthorized'}).encode()
                return
            try:
                data = json.loads(flow.request.content.decode())
                token = data.get('token')
                if token:
                    flow.response.content = json.dumps(decode_jwt(token)).encode()
                else:
                    flow.response.content = json.dumps({'error': 'No token'}).encode()
            except Exception as e:
                flow.response.content = json.dumps({'error': str(e)}).encode()
            return
        
        # POST /api/users
        if method == "POST" and path == "/api/users":
            if not auth_token or not verify_token(auth_token)[0]:
                flow.response.status_code = 401
                flow.response.content = json.dumps({'error': 'Unauthorized'}).encode()
                return
            try:
                data = json.loads(flow.request.content.decode())
                uid = data.get('uid')
                jwt = data.get('jwt')
                if uid and jwt:
                    uid_jwt_cache[uid] = jwt
                    if save_uid_jwt_mapping():
                        flow.response.content = json.dumps({'success': True, 'message': f'User {uid} saved'}).encode()
                    else:
                        flow.response.status_code = 500
                        flow.response.content = json.dumps({'success': False, 'message': 'Save failed'}).encode()
                else:
                    flow.response.status_code = 400
                    flow.response.content = json.dumps({'success': False, 'message': 'UID and JWT required'}).encode()
            except Exception as e:
                flow.response.status_code = 500
                flow.response.content = json.dumps({'error': str(e)}).encode()
            return
        
        # DELETE /api/users/{uid}
        if method == "DELETE" and path.startswith("/api/users/"):
            if not auth_token or not verify_token(auth_token)[0]:
                flow.response.status_code = 401
                flow.response.content = json.dumps({'error': 'Unauthorized'}).encode()
                return
            uid = path.split("/")[-1]
            if uid in uid_jwt_cache:
                del uid_jwt_cache[uid]
                if save_uid_jwt_mapping():
                    flow.response.content = json.dumps({'success': True, 'message': f'User {uid} deleted'}).encode()
                else:
                    flow.response.status_code = 500
                    flow.response.content = json.dumps({'success': False, 'message': 'Delete failed'}).encode()
            else:
                flow.response.status_code = 404
                flow.response.content = json.dumps({'success': False, 'message': 'User not found'}).encode()
            return
        
        flow.response.status_code = 404
        flow.response.content = json.dumps({'error': 'Not found'}).encode()
    
    def response(self, flow: http.HTTPFlow) -> None:
        try:
            if flow.request.method.upper() == "POST" and "majorlogin" in flow.request.path.lower():
                resp_bytes = flow.response.content
                uid_str = extract_uid_from_login_response(resp_bytes)
                
                if uid_str:
                    print(f"\n[UID] Found UID: {uid_str}")
                    if checkUIDExists(uid_str):
                        user_jwt = get_jwt_for_uid(uid_str)
                        if user_jwt:
                            print(f"[ALLOW] UID {uid_str} authorized")
                            self.valid_uid_detected = True
                            self.current_uid = uid_str
                            self.current_jwt = user_jwt
                        else:
                            self.valid_uid_detected = False
                    else:
                        new_response_bytes = bytes.fromhex("6a0a0891a40118f697fcc4067a020801")
                        flow.response.content = new_response_bytes
                        flow.response.status_code = 200
                        flow.response.headers["Content-Length"] = str(len(new_response_bytes))
                        print(f"[BLOCK] UID {uid_str} not authorized")
                        self.valid_uid_detected = False
                        self.current_uid = None
                        self.current_jwt = None
                else:
                    self.valid_uid_detected = False
            
            if flow.request.method.upper() == "POST" and "GetAccountBriefInfoBeforeLogin" in flow.request.path:
                if self.valid_uid_detected:
                    try:
                        data = flow.response.content
                        nickname = "Unknown"
                        reason = "UID not registered"
                        pos = 0
                        while pos < len(data) - 1:
                            if data[pos] == 0x12:
                                pos += 1
                                length = 0
                                shift = 0
                                while pos < len(data):
                                    byte = data[pos]
                                    length |= (byte & 0x7F) << shift
                                    pos += 1
                                    shift += 7
                                    if not (byte & 0x80):
                                        break
                                if pos + length <= len(data):
                                    nickname = data[pos:pos + length].decode('utf-8', errors='ignore')
                                    break
                            pos += 1
                    except Exception as e:
                        print(f"[Brief] Error: {e}")
                    
                    new_content = modify_get_account_response(flow.response.content, nickname, reason)
                    flow.response.content = new_content
                    flow.response.headers["Content-Length"] = str(len(new_content))
        except Exception as e:
            print(f"[ERROR] {e}")

addons = [UIDJWTManager()]

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║                    UID/JWT Manager v5.0                         ║
    ║                   (Advanced Token System)                        ║
    ║                          Starting on port 20335                  ║
    ╠══════════════════════════════════════════════════════════════════╣
    ║  Token Generation URLs:                                         ║
    ║  • Web UI:     http://localhost:20335/token                     ║
    ║  • API:        http://localhost:20335/api/generate_token        ║
    ║  • Simple:     http://localhost:20335/generate                  ║
    ║  • Unlimited:  http://localhost:20335/generate?unlimited        ║
    ║  • 30 Days:    http://localhost:20335/generate?30day            ║
    ║                                                                  ║
    ║  Default Password: test                                         ║
    ║                                                                  ║
    ║  Press Ctrl+C to stop                                           ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)
    
    from mitmproxy.tools.main import mitmweb
    
    sys.argv = [
        "mitmweb",
        "-s", __file__,
        "-p", "20335",
        "--set", "block_global=false",
        "--web-host", "0.0.0.0"
    ]
    
    try:
        mitmweb()
    except KeyboardInterrupt:
        print("\n[INFO] Shutting down...")
        sys.exit(0)