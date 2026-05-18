from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
import os
import zipfile
import subprocess
import shutil
import json
from datetime import datetime
import sys
import time
import threading
import atexit

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "BISHAL_hosting_secret_key_2024")

UPLOAD_FOLDER = "servers"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Track processes by user and server name
processes = {}

# Cleanup function for server deletion
def force_delete_directory(path, max_retries=5, delay=1):
    """Force delete directory with retries"""
    for i in range(max_retries):
        try:
            if os.path.exists(path):
                shutil.rmtree(path, ignore_errors=True)
                return True
        except Exception as e:
            print(f"Attempt {i+1} failed: {str(e)}")
            time.sleep(delay)
    return False

# Cleanup on exit
@atexit.register
def cleanup_on_exit():
    """Cleanup all processes when app exits"""
    for (username, server_name), process in list(processes.items()):
        try:
            if process.poll() is None:
                process.terminate()
                time.sleep(0.5)
                if process.poll() is None:
                    process.kill()
        except:
            pass

# ---------- Helper Functions ----------

def get_user_server_path():
    """Get the current user's server folder path"""
    if 'username' not in session:
        return None
    user_dir = os.path.join(UPLOAD_FOLDER, session['username'])
    os.makedirs(user_dir, exist_ok=True)
    return user_dir

def extract_zip(zip_path, extract_to):
    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall(extract_to)

def install_requirements(path):
    req = os.path.join(path, "requirements.txt")
    if os.path.exists(req):
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", req],
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode != 0:
                print(f"Requirements installation failed: {result.stderr}")
        except subprocess.TimeoutExpired:
            print("Requirements installation timed out")
        except Exception as e:
            print(f"Error installing requirements: {str(e)}")

def find_main_file(path):
    """Find the main Python file in a directory"""
    common_files = ["main.py", "app.py", "bot.py", "server.py", "index.py", "start.py"]
    for filename in common_files:
        if os.path.exists(os.path.join(path, filename)):
            return filename
    
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith('.py') and not file.startswith('_'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if '__main__' in content or 'if __name__' in content:
                            return file
                except:
                    continue
    return None

def save_server_config(username, server_name, config):
    config_path = os.path.join(UPLOAD_FOLDER, username, server_name, "config.json")
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

def load_server_config(username, server_name):
    config_path = os.path.join(UPLOAD_FOLDER, username, server_name, "config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except:
            pass
    return {"status": "stopped", "type": "web", "port": 8080, "created_at": str(datetime.now())}

def start_server(server_name):
    try:
        user_dir = get_user_server_path()
        if not user_dir:
            return False
            
        server_dir = os.path.join(user_dir, server_name)
        
        if not os.path.exists(server_dir):
            print(f"[ERROR] Server directory not found: {server_dir}")
            return False
        
        config = load_server_config(session['username'], server_name)
        log_path = os.path.join(server_dir, "logs.txt")
        
        with open(log_path, 'a', encoding='utf-8') as log:
            log.write(f"\n{'='*60}\n")
            log.write(f"Starting server: {server_name} at {datetime.now()}\n")
            
            zip_path = os.path.join(server_dir, "server.zip")
            extract_dir = os.path.join(server_dir, "extracted")
            
            if os.path.exists(zip_path):
                log.write(f"Found ZIP file: {zip_path}\n")
                if not os.path.exists(extract_dir):
                    os.makedirs(extract_dir, exist_ok=True)
                    log.write(f"Extracting to: {extract_dir}\n")
                    try:
                        extract_zip(zip_path, extract_dir)
                        install_requirements(extract_dir)
                    except Exception as e:
                        log.write(f"Error extracting/installing: {str(e)}\n")
                working_dir = extract_dir
            else:
                log.write("No ZIP file found, using server directory directly\n")
                working_dir = server_dir
                install_requirements(working_dir)
            
            main_file = find_main_file(working_dir)
            if not main_file:
                test_file = os.path.join(working_dir, "test_server.py")
                if not os.path.exists(test_file):
                    with open(test_file, 'w') as f:
                        f.write("""
from flask import Flask
import time

app = Flask(__name__)

@app.route('/')
def home():
    return f"<h1>BISHAL Hosting Test Server</h1><p>Running at {time.ctime()}</p>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
""")
                main_file = "test_server.py"
            
            log.write(f"Found main file: {main_file}\n")
            
            python_cmd = "python3" if shutil.which("python3") else "python"
            cmd = [python_cmd, main_file]
            
            if config.get('type') == 'web':
                port = config.get('port', 8080)
                log.write(f"Web server starting on port: {port}\n")
            
            log.write(f"Command: {' '.join(cmd)}\n")
            log.write(f"Working directory: {working_dir}\n")
            log.write(f"{'='*60}\n")
        
        log_file = open(log_path, 'a', encoding='utf-8')
        
        try:
            p = subprocess.Popen(
                cmd,
                cwd=working_dir,
                stdout=log_file,
                stderr=log_file,
                shell=False,
                start_new_session=True
            )
            
            processes[(session['username'], server_name)] = p
            
            config['status'] = 'running'
            config['pid'] = p.pid
            config['started_at'] = str(datetime.now())
            save_server_config(session['username'], server_name, config)
            
            def monitor_process(proc, key):
                proc.wait()
                if key in processes:
                    processes.pop(key, None)
                config = load_server_config(session['username'], server_name)
                config['status'] = 'stopped'
                config.pop('pid', None)
                save_server_config(session['username'], server_name, config)
            
            monitor_thread = threading.Thread(
                target=monitor_process,
                args=(p, (session['username'], server_name)),
                daemon=True
            )
            monitor_thread.start()
            
            return True
                
        except Exception as e:
            log_file.write(f"[ERROR] Failed to start process: {str(e)}\n")
            log_file.close()
            return False
            
    except Exception as e:
        print(f"[ERROR in start_server]: {str(e)}")
        return False

def stop_server(server_name):
    key = (session['username'], server_name)
    p = processes.get(key)
    
    if p:
        try:
            print(f"[INFO] Stopping server {server_name} with PID: {p.pid}")
            p.terminate()
            time.sleep(2)
            
            if p.poll() is None:
                p.kill()
                time.sleep(1)
            
            processes.pop(key, None)
            
            config = load_server_config(session['username'], server_name)
            config['status'] = 'stopped'
            config.pop('pid', None)
            save_server_config(session['username'], server_name, config)
            
            return True
        except Exception as e:
            print(f"[ERROR stopping server]: {str(e)}")
            return False
    
    return True

# ---------- Routes ----------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        # Default credentials: username: admin, password: admin123
        if username and password:
            if username == "admin" and password == "admin123":
                session['username'] = username
                return redirect(url_for("dashboard"))
            else:
                return '''
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>BISHAL Hosting | Login Failed</title>
                    <style>
                        * { margin: 0; padding: 0; box-sizing: border-box; }
                        body {
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            font-family: 'Montserrat', sans-serif;
                            height: 100vh;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                        }
                        .error-box {
                            background: rgba(0,0,0,0.8);
                            padding: 40px;
                            border-radius: 20px;
                            text-align: center;
                            color: white;
                        }
                        .error-box h2 { color: #ff4757; margin-bottom: 20px; }
                        .error-box a { color: #00d4ff; text-decoration: none; }
                    </style>
                </head>
                <body>
                    <div class="error-box">
                        <h2>Login Failed!</h2>
                        <p>Invalid username or password.</p>
                        <a href="/login">Try Again</a>
                    </div>
                </body>
                </html>
                '''
    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>BISHAL Hosting | Login</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                background-color: #050505;
                color: #ffffff;
                font-family: 'Montserrat', sans-serif;
                overflow: hidden;
                height: 100vh;
                width: 100vw;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }
            .login-container {
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                text-align: center;
                z-index: 1;
                width: 90%;
                max-width: 400px;
                padding: 40px;
                background: rgba(0, 0, 0, 0.8);
                border-radius: 20px;
                box-shadow: 0 0 50px rgba(157, 0, 255, 0.3);
                backdrop-filter: blur(10px);
            }
            .logo {
                font-size: 2.5rem;
                font-weight: 700;
                margin-bottom: 10px;
                background: linear-gradient(to right, #9d00ff, #00d4ff);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                text-transform: uppercase;
                letter-spacing: 3px;
            }
            .tagline {
                color: #aaa;
                margin-bottom: 30px;
                font-size: 0.9rem;
            }
            input[type="text"], input[type="password"] {
                width: 100%;
                padding: 15px;
                margin-bottom: 20px;
                border: 2px solid #9d00ff;
                border-radius: 10px;
                background: rgba(255, 255, 255, 0.05);
                color: white;
                font-size: 1rem;
                transition: all 0.3s;
            }
            input[type="text"]:focus, input[type="password"]:focus {
                outline: none;
                border-color: #00d4ff;
                box-shadow: 0 0 15px rgba(0, 212, 255, 0.5);
            }
            button {
                width: 100%;
                padding: 15px;
                border: 2px solid #9d00ff;
                background: linear-gradient(45deg, #9d00ff, #00d4ff);
                color: white;
                border-radius: 10px;
                font-size: 1rem;
                font-weight: bold;
                cursor: pointer;
                transition: all 0.3s;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            button:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 20px rgba(157, 0, 255, 0.4);
            }
            .particles {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                z-index: -1;
            }
            .info {
                margin-top: 20px;
                color: #666;
                font-size: 0.8rem;
            }
            .info p {
                margin: 5px 0;
            }
        </style>
    </head>
    <body>
        <div class="particles" id="particles"></div>
        <div class="login-container">
            <div class="logo">BISHAL Hosting</div>
            <div class="tagline">Unlimited Server Hosting - Free Forever</div>
            <form method="POST">
                <input type="text" name="username" placeholder="Username" required>
                <input type="password" name="password" placeholder="Password" required>
                <button type="submit">Login</button>
            </form>
            <div class="info">
                <p>Demo Credentials:</p>
                <p>Username: <strong style="color:#00d4ff">admin</strong> | Password: <strong style="color:#00d4ff">admin123</strong></p>
            </div>
        </div>
        <script>
            const canvas = document.getElementById('particles');
            const ctx = canvas.getContext('2d');
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
            
            let particles = [];
            for(let i = 0; i < 50; i++) {
                particles.push({
                    x: Math.random() * canvas.width,
                    y: Math.random() * canvas.height,
                    radius: Math.random() * 2 + 1,
                    speedX: Math.random() * 0.5 - 0.25,
                    speedY: Math.random() * 0.5 - 0.25
                });
            }
            
            function animate() {
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                ctx.fillStyle = 'rgba(157, 0, 255, 0.5)';
                
                particles.forEach(p => {
                    p.x += p.speedX;
                    p.y += p.speedY;
                    
                    if(p.x < 0) p.x = canvas.width;
                    if(p.x > canvas.width) p.x = 0;
                    if(p.y < 0) p.y = canvas.height;
                    if(p.y > canvas.height) p.y = 0;
                    
                    ctx.beginPath();
                    ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
                    ctx.fill();
                });
                
                requestAnimationFrame(animate);
            }
            animate();
        </script>
    </body>
    </html>
    '''

@app.route("/logout")
def logout():
    if 'username' in session:
        username = session['username']
        servers_to_stop = [(user, name) for (user, name) in list(processes.keys()) if user == username]
        for (user, server_name) in servers_to_stop:
            stop_server(server_name)
        time.sleep(1)
    
    session.clear()
    return redirect(url_for("login"))

@app.route("/", methods=["GET", "POST"])
def dashboard():
    if 'username' not in session:
        return redirect(url_for("login"))

    user_dir = get_user_server_path()
    
    if request.method == "POST":
        action = request.form.get("action")
        
        if action == "create_server":
            server_name = request.form.get("server_name", "").strip()
            server_type = request.form.get("server_type", "web")
            port = request.form.get("port", "8080")
            
            if server_name:
                safe_name = server_name.replace(" ", "_").replace("/", "_").replace("\\", "_")
                server_dir = os.path.join(user_dir, safe_name)
                
                if not os.path.exists(server_dir):
                    os.makedirs(server_dir, exist_ok=True)
                    
                    config = {
                        "name": server_name,
                        "display_name": server_name,
                        "safe_name": safe_name,
                        "type": server_type,
                        "port": int(port) if port.isdigit() else 8080,
                        "status": "stopped",
                        "created_at": str(datetime.now())
                    }
                    save_server_config(session['username'], safe_name, config)
                    
                    file = request.files.get("server_files")
                    if file and file.filename:
                        filename = file.filename
                        if filename.endswith(".zip"):
                            file.save(os.path.join(server_dir, "server.zip"))
                        else:
                            file.save(os.path.join(server_dir, filename))

    servers = []
    if os.path.exists(user_dir):
        for folder_name in os.listdir(user_dir):
            server_dir = os.path.join(user_dir, folder_name)
            if not os.path.isdir(server_dir): 
                continue
            
            config = load_server_config(session['username'], folder_name)
            
            log_file = os.path.join(server_dir, "logs.txt")
            log_data = ""
            if os.path.exists(log_file):
                try:
                    with open(log_file, "r", errors="ignore", encoding='utf-8') as f:
                        content = f.read()
                        log_data = content[-2000:] if len(content) > 2000 else content
                except:
                    log_data = "Error reading log file"

            has_files = (
                os.path.exists(os.path.join(server_dir, "server.zip")) or 
                any(f.endswith('.py') for f in os.listdir(server_dir) if os.path.isfile(os.path.join(server_dir, f)))
            )

            servers.append({
                "name": folder_name,
                "display_name": config.get("display_name", folder_name),
                "running": (session['username'], folder_name) in processes,
                "log": log_data,
                "config": config,
                "has_files": has_files,
                "created_at": config.get("created_at", "Unknown")
            })

    servers.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    return render_template_string(DASHBOARD_HTML, servers=servers, session=session)

@app.route("/api/server/<action>/<name>", methods=["POST"])
def server_action(action, name):
    if 'username' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    server_name = name.strip()
    
    if action == "start":
        user_dir = get_user_server_path()
        server_dir = os.path.join(user_dir, server_name)
        
        if not os.path.exists(server_dir):
            return jsonify({"error": f"Server '{server_name}' not found"}), 404
        
        if (session['username'], server_name) in processes:
            return jsonify({"error": "Server is already running"}), 400
        
        if start_server(server_name):
            return jsonify({"success": True, "message": f"Server '{server_name}' started successfully"})
        else:
            return jsonify({"error": f"Failed to start server '{server_name}'. Check logs for details."}), 400
    
    elif action == "stop":
        if stop_server(server_name):
            return jsonify({"success": True, "message": f"Server '{server_name}' stopped"})
        else:
            return jsonify({"error": f"Failed to stop server '{server_name}'"}), 400
    
    elif action == "restart":
        stop_server(server_name)
        time.sleep(2)
        if start_server(server_name):
            return jsonify({"success": True, "message": f"Server '{server_name}' restarted"})
        else:
            return jsonify({"error": f"Failed to restart server '{server_name}'"}), 400
    
    elif action == "delete":
        stop_server(server_name)
        time.sleep(1)
        
        user_dir = get_user_server_path()
        server_dir = os.path.join(user_dir, server_name)
        
        if os.path.exists(server_dir):
            try:
                if force_delete_directory(server_dir):
                    key = (session['username'], server_name)
                    if key in processes:
                        processes.pop(key, None)
                    return jsonify({"success": True, "message": f"Server '{server_name}' deleted successfully"})
                else:
                    return jsonify({"error": f"Failed to delete server directory after multiple attempts"}), 400
            except Exception as e:
                return jsonify({"error": f"Failed to delete server: {str(e)}"}), 400
        else:
            return jsonify({"error": f"Server '{server_name}' not found"}), 404
    
    return jsonify({"error": "Invalid action"}), 400

@app.route("/api/logs/<name>")
def get_logs(name):
    if 'username' not in session:
        return "", 401
    
    server_name = name.strip()
    user_dir = get_user_server_path()
    server_dir = os.path.join(user_dir, server_name)
    log_file = os.path.join(server_dir, "logs.txt")
    
    if os.path.exists(log_file):
        try:
            with open(log_file, "r", errors="ignore", encoding='utf-8') as f:
                content = f.read()
                return content[-10000:] if len(content) > 10000 else content
        except:
            return "Error reading log file"
    return "No logs available"

@app.route("/api/servers")
def get_servers():
    if 'username' not in session:
        return jsonify([])
    
    user_dir = get_user_server_path()
    servers = []
    
    if os.path.exists(user_dir):
        for folder_name in os.listdir(user_dir):
            server_dir = os.path.join(user_dir, folder_name)
            if os.path.isdir(server_dir):
                config = load_server_config(session['username'], folder_name)
                servers.append({
                    "name": folder_name,
                    "display_name": config.get("display_name", folder_name),
                    "running": (session['username'], folder_name) in processes,
                    "config": config
                })
    
    return jsonify(servers)

@app.route("/api/stats")
def get_stats():
    if 'username' not in session:
        return jsonify({})
    
    user_dir = get_user_server_path()
    total_servers = 0
    running_servers = 0
    
    if os.path.exists(user_dir):
        for folder_name in os.listdir(user_dir):
            server_dir = os.path.join(user_dir, folder_name)
            if os.path.isdir(server_dir):
                total_servers += 1
                if (session['username'], folder_name) in processes:
                    running_servers += 1
    
    return jsonify({
        "total_servers": total_servers,
        "running_servers": running_servers,
        "unlimited": True,
        "message": "Unlimited servers available!"
    })

@app.route("/health")
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": str(datetime.now()),
        "total_processes": len(processes)
    })

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# Dashboard HTML Template
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BISHAL Hosting | Unlimited Server Hosting</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Poppins', sans-serif;
            background: #0a0f1f;
            color: #fff;
            overflow-x: hidden;
        }

        .blue-bg {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -2;
            background: linear-gradient(135deg, #0a0f1f 0%, #0a1a3a 50%, #0d2b4e 100%);
        }

        .particles {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -1;
        }

        .particle {
            position: absolute;
            background: rgba(0, 150, 255, 0.3);
            border-radius: 50%;
            animation: floatParticle linear infinite;
        }

        @keyframes floatParticle {
            0% {
                transform: translateY(100vh) rotate(0deg);
                opacity: 0;
            }
            10% {
                opacity: 1;
            }
            90% {
                opacity: 1;
            }
            100% {
                transform: translateY(-100vh) rotate(360deg);
                opacity: 0;
            }
        }

        .navbar {
            background: rgba(5, 10, 25, 0.95);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid rgba(0, 150, 255, 0.3);
            padding: 1rem 2rem;
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .nav-container {
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
        }

        .logo {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .logo-icon {
            width: 45px;
            height: 45px;
            background: linear-gradient(135deg, #0099ff, #0033cc);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            box-shadow: 0 0 20px rgba(0, 150, 255, 0.5);
            animation: logoGlow 2s ease-in-out infinite;
        }

        @keyframes logoGlow {
            0%, 100% {
                box-shadow: 0 0 20px rgba(0, 150, 255, 0.5);
            }
            50% {
                box-shadow: 0 0 40px rgba(0, 150, 255, 0.8);
            }
        }

        .logo-text {
            font-size: 1.6rem;
            font-weight: 800;
            font-family: 'Orbitron', monospace;
            background: linear-gradient(135deg, #0099ff, #00d4ff);
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .logo-badge {
            background: rgba(0, 150, 255, 0.2);
            border: 1px solid rgba(0, 150, 255, 0.5);
            color: #00d4ff;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.7rem;
            font-weight: 600;
            margin-left: 10px;
        }

        .user-section {
            display: flex;
            align-items: center;
            gap: 1.5rem;
        }

        .user-avatar {
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, #0099ff, #0033cc);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            box-shadow: 0 0 15px rgba(0, 150, 255, 0.4);
        }

        .username-display {
            color: #00d4ff;
            font-weight: 500;
        }

        .logout-btn {
            background: rgba(255, 71, 87, 0.15);
            border: 1px solid rgba(255, 71, 87, 0.4);
            color: #ff6b6b;
            padding: 8px 20px;
            border-radius: 25px;
            text-decoration: none;
            font-weight: 500;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .logout-btn:hover {
            background: rgba(255, 71, 87, 0.3);
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(255, 71, 87, 0.2);
        }

        .main-container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }

        .hero-section {
            text-align: center;
            margin-bottom: 3rem;
            padding: 2rem;
            background: linear-gradient(135deg, rgba(0, 100, 255, 0.1), rgba(0, 50, 150, 0.05));
            border-radius: 30px;
            border: 1px solid rgba(0, 150, 255, 0.2);
        }

        .hero-title {
            font-size: 3rem;
            font-weight: 800;
            font-family: 'Orbitron', monospace;
            margin-bottom: 1rem;
        }

        .hero-title span {
            background: linear-gradient(135deg, #0099ff, #00d4ff, #0066ff);
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .hero-subtitle {
            color: #8899bb;
            font-size: 1.1rem;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 1.5rem;
            margin-bottom: 3rem;
        }

        .stat-card {
            background: rgba(5, 10, 30, 0.6);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(0, 150, 255, 0.2);
            border-radius: 20px;
            padding: 1.5rem;
            transition: all 0.3s;
            position: relative;
            overflow: hidden;
        }

        .stat-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(0, 150, 255, 0.1), transparent);
            transition: left 0.5s;
        }

        .stat-card:hover::before {
            left: 100%;
        }

        .stat-card:hover {
            transform: translateY(-5px);
            border-color: rgba(0, 150, 255, 0.5);
            box-shadow: 0 10px 30px rgba(0, 100, 255, 0.2);
        }

        .stat-icon {
            font-size: 2.5rem;
            margin-bottom: 1rem;
            color: #0099ff;
        }

        .stat-value {
            font-size: 2.8rem;
            font-weight: 800;
            font-family: 'Orbitron', monospace;
            margin-bottom: 0.5rem;
            background: linear-gradient(135deg, #fff, #00d4ff);
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .stat-label {
            color: #8899bb;
            font-size: 0.9rem;
        }

        .unlimited-tag {
            display: inline-block;
            background: linear-gradient(135deg, #0099ff, #00d4ff);
            color: #fff;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.7rem;
            font-weight: 600;
            margin-top: 10px;
        }

        .create-section {
            background: rgba(5, 10, 30, 0.6);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(0, 150, 255, 0.2);
            border-radius: 24px;
            padding: 2rem;
            margin-bottom: 3rem;
            transition: all 0.3s;
        }

        .create-section:hover {
            border-color: rgba(0, 150, 255, 0.4);
            box-shadow: 0 5px 25px rgba(0, 100, 255, 0.15);
        }

        .section-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 2rem;
        }

        .section-header i {
            font-size: 2rem;
            color: #0099ff;
        }

        .section-header h2 {
            font-size: 1.8rem;
            font-weight: 600;
        }

        .form-row {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 1.5rem;
        }

        .input-group {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }

        .input-group label {
            color: #8899bb;
            font-size: 0.85rem;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .input-group input,
        .input-group select {
            background: rgba(0, 0, 0, 0.5);
            border: 1px solid rgba(0, 150, 255, 0.3);
            border-radius: 12px;
            padding: 12px 16px;
            color: white;
            font-family: 'Poppins', sans-serif;
            transition: all 0.3s;
        }

        .input-group input:focus,
        .input-group select:focus {
            outline: none;
            border-color: #0099ff;
            box-shadow: 0 0 0 3px rgba(0, 150, 255, 0.1);
        }

        .upload-area {
            border: 2px dashed rgba(0, 150, 255, 0.3);
            border-radius: 16px;
            padding: 2rem;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
            margin: 1.5rem 0;
        }

        .upload-area:hover {
            border-color: #0099ff;
            background: rgba(0, 150, 255, 0.05);
        }

        .upload-area i {
            font-size: 3rem;
            color: #0099ff;
            margin-bottom: 1rem;
        }

        .create-btn {
            width: 100%;
            background: linear-gradient(135deg, #0099ff, #0033cc);
            border: none;
            padding: 14px;
            border-radius: 12px;
            color: white;
            font-weight: 600;
            font-size: 1rem;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            position: relative;
            overflow: hidden;
        }

        .create-btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
            transition: left 0.5s;
        }

        .create-btn:hover::before {
            left: 100%;
        }

        .create-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(0, 100, 255, 0.4);
        }

        .servers-section {
            background: rgba(5, 10, 30, 0.6);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(0, 150, 255, 0.2);
            border-radius: 24px;
            padding: 2rem;
        }

        .servers-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
            gap: 1.5rem;
            margin-top: 1.5rem;
        }

        .server-card {
            background: rgba(0, 0, 0, 0.4);
            border: 1px solid rgba(0, 150, 255, 0.15);
            border-radius: 16px;
            overflow: hidden;
            transition: all 0.3s;
            position: relative;
        }

        .server-card:hover {
            transform: translateY(-5px);
            border-color: rgba(0, 150, 255, 0.4);
            box-shadow: 0 10px 25px rgba(0, 100, 255, 0.2);
        }

        .server-card.running {
            border-left: 3px solid #00ff88;
        }

        .server-card-header {
            padding: 1.25rem;
            background: linear-gradient(135deg, rgba(0, 50, 150, 0.3), rgba(0, 0, 0, 0.5));
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid rgba(0, 150, 255, 0.1);
        }

        .server-info h3 {
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 4px;
        }

        .server-date {
            font-size: 0.7rem;
            color: #6688aa;
        }

        .status-badge {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.7rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 5px;
        }

        .status-badge.running {
            background: rgba(0, 255, 136, 0.15);
            color: #00ff88;
            border: 1px solid rgba(0, 255, 136, 0.3);
        }

        .status-badge.stopped {
            background: rgba(255, 71, 87, 0.15);
            color: #ff6b6b;
            border: 1px solid rgba(255, 71, 87, 0.3);
        }

        .server-details {
            padding: 1rem 1.25rem;
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
            border-bottom: 1px solid rgba(0, 150, 255, 0.1);
        }

        .detail-item {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 0.85rem;
            color: #8899bb;
        }

        .detail-item i {
            width: 20px;
            color: #0099ff;
        }

        .server-actions {
            padding: 1rem 1.25rem;
            display: flex;
            gap: 0.75rem;
            flex-wrap: wrap;
        }

        .action-btn {
            padding: 8px 16px;
            border-radius: 10px;
            font-size: 0.8rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: transparent;
            border: 1px solid;
        }

        .action-btn.start {
            border-color: #00ff88;
            color: #00ff88;
        }

        .action-btn.start:hover {
            background: rgba(0, 255, 136, 0.1);
            transform: scale(1.02);
        }

        .action-btn.stop {
            border-color: #ff4757;
            color: #ff4757;
        }

        .action-btn.stop:hover {
            background: rgba(255, 71, 87, 0.1);
            transform: scale(1.02);
        }

        .action-btn.restart {
            border-color: #ffaa00;
            color: #ffaa00;
        }

        .action-btn.restart:hover {
            background: rgba(255, 170, 0, 0.1);
            transform: scale(1.02);
        }

        .action-btn.logs {
            border-color: #00d4ff;
            color: #00d4ff;
        }

        .action-btn.logs:hover {
            background: rgba(0, 212, 255, 0.1);
            transform: scale(1.02);
        }

        .action-btn.delete {
            border-color: #ff4757;
            color: #ff4757;
        }

        .action-btn.delete:hover {
            background: rgba(255, 71, 87, 0.1);
            transform: scale(1.02);
        }

        .action-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }

        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.95);
            backdrop-filter: blur(10px);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }

        .modal.active {
            display: flex;
        }

        .modal-content {
            width: 90%;
            max-width: 900px;
            height: 80vh;
            background: #0a0f1f;
            border: 1px solid rgba(0, 150, 255, 0.3);
            border-radius: 20px;
            overflow: hidden;
        }

        .modal-header {
            padding: 1rem 1.5rem;
            background: rgba(0, 50, 150, 0.3);
            border-bottom: 1px solid rgba(0, 150, 255, 0.2);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .modal-header h3 {
            display: flex;
            align-items: center;
            gap: 10px;
            color: #00d4ff;
        }

        .modal-close {
            background: none;
            border: none;
            color: #aaa;
            font-size: 1.5rem;
            cursor: pointer;
            transition: color 0.3s;
        }

        .modal-close:hover {
            color: #ff4757;
        }

        .modal-body {
            padding: 1rem;
            height: calc(100% - 60px);
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 0.8rem;
            background: #050a15;
        }

        .log-line {
            padding: 4px 0;
            border-bottom: 1px solid rgba(0, 150, 255, 0.1);
            white-space: pre-wrap;
            word-break: break-all;
        }

        .toast {
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: rgba(5, 10, 30, 0.95);
            backdrop-filter: blur(10px);
            border-left: 3px solid;
            padding: 12px 20px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            gap: 12px;
            z-index: 1100;
            animation: slideIn 0.3s ease;
        }

        .toast.success {
            border-color: #00ff88;
        }

        .toast.error {
            border-color: #ff4757;
        }

        .toast.info {
            border-color: #0099ff;
        }

        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }

        .empty-state {
            text-align: center;
            padding: 4rem;
            color: #6688aa;
        }

        .empty-state i {
            font-size: 4rem;
            margin-bottom: 1rem;
            opacity: 0.3;
        }

        @media (max-width: 768px) {
            .nav-container {
                flex-direction: column;
                text-align: center;
            }
            .main-container {
                padding: 1rem;
            }
            .servers-grid {
                grid-template-columns: 1fr;
            }
            .form-row {
                grid-template-columns: 1fr;
            }
            .hero-title {
                font-size: 2rem;
            }
        }

        .spinner {
            width: 16px;
            height: 16px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-top-color: white;
            border-radius: 50%;
            animation: spin 0.6s linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        ::-webkit-scrollbar {
            width: 8px;
        }
        ::-webkit-scrollbar-track {
            background: #0a0f1f;
        }
        ::-webkit-scrollbar-thumb {
            background: #0099ff;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <div class="blue-bg"></div>
    <div class="particles" id="particles"></div>

    <nav class="navbar">
        <div class="nav-container">
            <div class="logo">
                <div class="logo-icon">
                    <i class="fas fa-cube"></i>
                </div>
                <div>
                    <span class="logo-text">BISHAL</span>
                    <span class="logo-badge">UNLIMITED</span>
                </div>
            </div>
            <div class="user-section">
                <div class="user-avatar">
                    <i class="fas fa-user"></i>
                </div>
                <span class="username-display">{{ session['username'] }}</span>
                <a href="/logout" class="logout-btn">
                    <i class="fas fa-sign-out-alt"></i> Logout
                </a>
            </div>
        </div>
    </nav>

    <div class="main-container">
        <div class="hero-section">
            <h1 class="hero-title">BISHAL <span>Unlimited</span> Hosting</h1>
            <p class="hero-subtitle">Free forever • No limits • High performance</p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-icon">
                    <i class="fas fa-server"></i>
                </div>
                <div class="stat-value" id="totalServers">0</div>
                <div class="stat-label">Total Servers</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">
                    <i class="fas fa-play-circle"></i>
                </div>
                <div class="stat-value" id="runningServers">0</div>
                <div class="stat-label">Running Servers</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">
                    <i class="fas fa-infinity"></i>
                </div>
                <div class="stat-value">∞</div>
                <div class="stat-label">Server Limit</div>
                <span class="unlimited-tag">UNLIMITED</span>
            </div>
            <div class="stat-card">
                <div class="stat-icon">
                    <i class="fas fa-gem"></i>
                </div>
                <div class="stat-value">FREE</div>
                <div class="stat-label">Forever Free</div>
                <span class="unlimited-tag">NO CHARGES</span>
            </div>
        </div>

        <div class="create-section">
            <div class="section-header">
                <i class="fas fa-plus-circle"></i>
                <h2>Create New Server</h2>
            </div>
            
            <form id="createForm" method="POST" enctype="multipart/form-data">
                <input type="hidden" name="action" value="create_server">
                
                <div class="form-row">
                    <div class="input-group">
                        <label><i class="fas fa-tag"></i> Server Name</label>
                        <input type="text" name="server_name" id="serverName" placeholder="e.g., my-awesome-bot" required>
                    </div>
                    <div class="input-group">
                        <label><i class="fas fa-code-branch"></i> Server Type</label>
                        <select name="server_type" id="serverType">
                            <option value="web">🌐 Web Application</option>
                            <option value="bot">🤖 Bot Application</option>
                            <option value="api">⚡ API Server</option>
                            <option value="custom">🔧 Custom Application</option>
                        </select>
                    </div>
                    <div class="input-group">
                        <label><i class="fas fa-plug"></i> Port</label>
                        <input type="number" name="port" id="port" value="8080" min="1024" max="65535">
                    </div>
                </div>

                <div class="upload-area" id="uploadArea">
                    <i class="fas fa-cloud-upload-alt"></i>
                    <p><strong>Upload Your Files</strong></p>
                    <p>ZIP file or Python files (.py)</p>
                    <small>Max file size: 100MB</small>
                    <input type="file" name="server_files" id="fileInput" style="display: none;" accept=".zip,.py">
                </div>

                <button type="submit" class="create-btn" id="createBtn">
                    <i class="fas fa-plus"></i>
                    <span>Create Server</span>
                </button>
            </form>
        </div>

        <div class="servers-section">
            <div class="section-header">
                <i class="fas fa-list"></i>
                <h2>Your Servers</h2>
            </div>

            <div class="servers-grid" id="serversGrid">
                {% for server in servers %}
                <div class="server-card {% if server.running %}running{% endif %}" data-server="{{ server.name }}">
                    <div class="server-card-header">
                        <div class="server-info">
                            <h3>{{ server.display_name }}</h3>
                            <div class="server-date">
                                <i class="far fa-calendar-alt"></i> {{ server.created_at[:10] if server.created_at else 'New' }}
                            </div>
                        </div>
                        <div class="status-badge {% if server.running %}running{% else %}stopped{% endif %}">
                            <i class="fas fa-circle"></i>
                            {% if server.running %}RUNNING{% else %}STOPPED{% endif %}
                        </div>
                    </div>
                    <div class="server-details">
                        <div class="detail-item">
                            <i class="fas fa-cube"></i>
                            <span>{{ server.config.type|upper }}</span>
                        </div>
                        <div class="detail-item">
                            <i class="fas fa-network-wired"></i>
                            <span>Port: {{ server.config.port }}</span>
                        </div>
                        <div class="detail-item">
                            <i class="fas {% if server.has_files %}fa-check-circle{% else %}fa-times-circle{% endif %}" style="color: {% if server.has_files %}#00ff88{% else %}#ff4757{% endif %}"></i>
                            <span>Files: {% if server.has_files %}Uploaded{% else %}None{% endif %}</span>
                        </div>
                    </div>
                    <div class="server-actions">
                        {% if server.running %}
                        <button class="action-btn stop" onclick="controlServer('{{ server.name }}', 'stop')">
                            <i class="fas fa-stop"></i> Stop
                        </button>
                        {% else %}
                        <button class="action-btn start" onclick="controlServer('{{ server.name }}', 'start')">
                            <i class="fas fa-play"></i> Start
                        </button>
                        {% endif %}
                        <button class="action-btn restart" onclick="controlServer('{{ server.name }}', 'restart')">
                            <i class="fas fa-sync-alt"></i> Restart
                        </button>
                        <button class="action-btn logs" onclick="showLogs('{{ server.name }}')">
                            <i class="fas fa-terminal"></i> Logs
                        </button>
                        <button class="action-btn delete" onclick="deleteServer('{{ server.name }}')">
                            <i class="fas fa-trash"></i> Delete
                        </button>
                    </div>
                </div>
                {% endfor %}
            </div>

            {% if not servers %}
            <div class="empty-state">
                <i class="fas fa-server"></i>
                <h3>No Servers Yet</h3>
                <p>Create your first server using the form above!</p>
            </div>
            {% endif %}
        </div>
    </div>

    <div class="modal" id="logModal">
        <div class="modal-content">
            <div class="modal-header">
                <h3><i class="fas fa-terminal"></i> <span id="modalServerName">Server Logs</span></h3>
                <button class="modal-close" onclick="closeLogModal()">&times;</button>
            </div>
            <div class="modal-body" id="logContent">
                <div style="color: #6688aa; text-align: center; padding: 2rem;">
                    <i class="fas fa-spinner fa-spin"></i> Loading logs...
                </div>
            </div>
        </div>
    </div>

    <script>
        function createParticles() {
            const container = document.getElementById('particles');
            const particleCount = 50;
            
            for (let i = 0; i < particleCount; i++) {
                const particle = document.createElement('div');
                particle.classList.add('particle');
                const size = Math.random() * 4 + 2;
                particle.style.width = size + 'px';
                particle.style.height = size + 'px';
                particle.style.left = Math.random() * 100 + '%';
                particle.style.animationDuration = Math.random() * 10 + 5 + 's';
                particle.style.animationDelay = Math.random() * 5 + 's';
                container.appendChild(particle);
            }
        }
        
        createParticles();

        let currentServer = null;
        let logInterval = null;

        function showToast(message, type = 'info') {
            const toast = document.createElement('div');
            toast.className = `toast ${type}`;
            toast.innerHTML = `
                <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'}"></i>
                <span>${message}</span>
            `;
            document.body.appendChild(toast);
            setTimeout(() => toast.remove(), 3000);
        }

        async function controlServer(serverName, action) {
            const btn = event.target.closest('button');
            
            if (btn) {
                btn.disabled = true;
                btn.innerHTML = '<span class="spinner"></span>';
            }

            try {
                const res = await fetch(`/api/server/${action}/${encodeURIComponent(serverName)}`, {
                    method: 'POST'
                });
                const data = await res.json();
                
                if (res.ok) {
                    showToast(data.message, 'success');
                    setTimeout(() => location.reload(), 1500);
                } else {
                    showToast(data.error || 'Operation failed', 'error');
                    if (btn) {
                        btn.innerHTML = btn.innerHTML.replace('<span class="spinner"></span>', 
                            action === 'start' ? '<i class="fas fa-play"></i> Start' : 
                            action === 'stop' ? '<i class="fas fa-stop"></i> Stop' : 
                            '<i class="fas fa-sync-alt"></i> Restart');
                        btn.disabled = false;
                    }
                }
            } catch (err) {
                showToast('Network error: ' + err.message, 'error');
                if (btn) {
                    btn.innerHTML = btn.innerHTML.replace('<span class="spinner"></span>', 
                        action === 'start' ? '<i class="fas fa-play"></i> Start' : 
                        action === 'stop' ? '<i class="fas fa-stop"></i> Stop' : 
                        '<i class="fas fa-sync-alt"></i> Restart');
                    btn.disabled = false;
                }
            }
        }

        async function deleteServer(serverName) {
            if (!confirm(`Are you sure you want to delete "${serverName}"?\nThis action cannot be undone!`)) {
                return;
            }

            showToast('Deleting server...', 'info');
            
            try {
                const res = await fetch(`/api/server/delete/${encodeURIComponent(serverName)}`, {
                    method: 'POST'
                });
                const data = await res.json();
                
                if (res.ok) {
                    showToast(data.message, 'success');
                    setTimeout(() => location.reload(), 1000);
                } else {
                    showToast(data.error || 'Failed to delete', 'error');
                }
            } catch (err) {
                showToast('Network error: ' + err.message, 'error');
            }
        }

        async function showLogs(serverName) {
            currentServer = serverName;
            document.getElementById('modalServerName').innerText = `${serverName} - Live Logs`;
            document.getElementById('logModal').classList.add('active');
            
            await loadLogs();
            
            if (logInterval) clearInterval(logInterval);
            logInterval = setInterval(loadLogs, 2000);
        }

        async function loadLogs() {
            if (!currentServer) return;
            
            try {
                const res = await fetch(`/api/logs/${encodeURIComponent(currentServer)}`);
                const logs = await res.text();
                const container = document.getElementById('logContent');
                
                const colored = logs.split('\n').map(line => {
                    let color = '#6688aa';
                    if (line.includes('ERROR') || line.toLowerCase().includes('error')) color = '#ff4757';
                    else if (line.includes('WARNING') || line.toLowerCase().includes('warning')) color = '#ffaa00';
                    else if (line.includes('INFO') || line.toLowerCase().includes('info')) color = '#00d4ff';
                    else if (line.includes('SUCCESS') || line.toLowerCase().includes('success')) color = '#00ff88';
                    else if (line.trim()) color = '#cccccc';
                    
                    return `<div class="log-line" style="color: ${color}">${escapeHtml(line) || '&nbsp;'}</div>`;
                }).join('');
                
                container.innerHTML = colored || '<div style="color: #6688aa;">No logs available</div>';
                container.scrollTop = container.scrollHeight;
            } catch (err) {
                console.error('Failed to load logs:', err);
            }
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        function closeLogModal() {
            document.getElementById('logModal').classList.remove('active');
            if (logInterval) {
                clearInterval(logInterval);
                logInterval = null;
            }
            currentServer = null;
        }

        async function updateStats() {
            try {
                const res = await fetch('/api/stats');
                const stats = await res.json();
                document.getElementById('totalServers').innerText = stats.total_servers || 0;
                document.getElementById('runningServers').innerText = stats.running_servers || 0;
            } catch (err) {
                console.error('Failed to update stats:', err);
            }
        }

        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        
        uploadArea.addEventListener('click', () => fileInput.click());
        
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.style.borderColor = '#00d4ff';
            uploadArea.style.background = 'rgba(0, 212, 255, 0.05)';
        });
        
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.style.borderColor = 'rgba(0, 150, 255, 0.3)';
            uploadArea.style.background = 'transparent';
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.style.borderColor = 'rgba(0, 150, 255, 0.3)';
            uploadArea.style.background = 'transparent';
            
            if (e.dataTransfer.files.length) {
                fileInput.files = e.dataTransfer.files;
                updateUploadLabel(e.dataTransfer.files[0].name);
            }
        });
        
        fileInput.addEventListener('change', () => {
            if (fileInput.files.length) {
                updateUploadLabel(fileInput.files[0].name);
            }
        });
        
        function updateUploadLabel(fileName) {
            uploadArea.innerHTML = `
                <i class="fas fa-check-circle" style="color: #00ff88;"></i>
                <p><strong>File Selected!</strong></p>
                <p>${fileName}</p>
                <small>Click to change</small>
                <input type="file" name="server_files" id="fileInput" style="display: none;" accept=".zip,.py">
            `;
            uploadArea.style.borderColor = '#00ff88';
            
            const newFileInput = document.getElementById('fileInput');
            if (newFileInput) {
                newFileInput.files = fileInput.files;
                newFileInput.addEventListener('change', () => {
                    if (newFileInput.files.length) {
                        updateUploadLabel(newFileInput.files[0].name);
                    }
                });
                const inputElement = uploadArea.querySelector('input');
                if (inputElement) {
                    inputElement.addEventListener('click', (e) => e.stopPropagation());
                }
            }
        }

        document.getElementById('createForm').addEventListener('submit', async (e) => {
            const serverName = document.getElementById('serverName').value.trim();
            if (!serverName) {
                e.preventDefault();
                showToast('Please enter a server name', 'error');
                return;
            }
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') closeLogModal();
        });
        
        document.getElementById('logModal').addEventListener('click', (e) => {
            if (e.target === document.getElementById('logModal')) closeLogModal();
        });

        setInterval(updateStats, 5000);
        updateStats();
        
        setTimeout(() => {
            showToast('🚀 Welcome to BISHAL Hosting! Deploy unlimited servers for free!', 'success');
        }, 1000);
    </script>
</body>
</html>
'''

if __name__ == "__main__":
    os.makedirs("templates", exist_ok=True)
    port = int(os.environ.get("PORT", 8030))
    
    print(f"""
    ╔══════════════════════════════════════════╗
    ║      BISHAL Hosting - Unlimited Servers    ║
    ║           Free Forever Edition           ║
    ╠══════════════════════════════════════════╣
    ║  • Server: http://0.0.0.0:{port}        ║
    ║  • Upload Folder: {UPLOAD_FOLDER}       ║
    ║  • No Server Limits!                    ║
    ║  • Press Ctrl+C to stop                 ║
    ╚══════════════════════════════════════════╝
    """)
    
    app.run(host="0.0.0.0", port=port, debug=True)