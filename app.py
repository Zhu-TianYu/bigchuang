from flask import Flask, Response, render_template, jsonify
import cv2
import zmq
import base64
import numpy as np
import time
import json
from openai import OpenAI

app = Flask(__name__)

# 全局复用 ZMQ Context
context = zmq.Context()

# 初始化 OpenAI 客户端 (Manus 环境已预配置)
client = OpenAI()

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/video_feed')
def video_feed():
    return Response(gen_display(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/ai_suggestion')
def ai_suggestion():
    """
    提供大模型生成的智能建议
    """
    # 模拟从实时数据中提取特征
    mock_data = {
        "brightness": round(np.random.uniform(70, 95), 2),
        "motion": round(np.random.uniform(20, 80), 2)
    }
    
    try:
        prompt = f"当前视频监控数据：亮度 {mock_data['brightness']}%，运动活跃度 {mock_data['motion']}%。请给出一条简短的专业监控建议（20字以内）。"
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50
        )
        suggestion = response.choices[0].message.content.strip()
    except Exception as e:
        suggestion = "系统建议：保持当前监控频率，定期检查设备。"
        
    return jsonify({
        "suggestion": suggestion,
        "data": mock_data
    })

def gen_display():
    footage_socket = context.socket(zmq.SUB)
    footage_socket.connect('tcp://127.0.0.1:5555')
    footage_socket.setsockopt_string(zmq.SUBSCRIBE, '')
    footage_socket.RCVTIMEO = 2000 

    while True:
        try:
            frame_str = footage_socket.recv_string()
            img_data = base64.b64decode(frame_str)
            npimg = np.frombuffer(img_data, dtype=np.uint8)
            frame = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
            
            if frame is None:
                continue
            
            ret, frame_encoded = cv2.imencode('.jpg', frame)
            if ret:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_encoded.tobytes() + b'\r\n')
            
        except zmq.Again:
            continue
        except Exception as e:
            print(f"Error: {e}")
            break
    
    footage_socket.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
