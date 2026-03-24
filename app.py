from flask import Flask, Response, render_template, jsonify
import cv2
import zmq
import base64
import numpy as np
import time
import json
from openai import OpenAI
from collections import deque

app = Flask(__name__)

# 全局变量
context = zmq.Context()
client = OpenAI()

# 用于存储最近的检测数据，供分析和可视化使用
detection_history = deque(maxlen=50) # 存储 (timestamp, count)
detection_logs = deque(maxlen=5) # 存储最近的日志条目

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/video_feed')
def video_feed():
    return Response(gen_display(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/ai_suggestion')
def ai_suggestion():
    """
    基于真实检测到的历史数据，生成智能监控建议
    """
    global detection_history, detection_logs
    
    # 提取最近的平均人数和活跃度
    if len(detection_history) > 0:
        avg_count = sum(c for t, c in detection_history) / len(detection_history)
        max_count = max(c for t, c in detection_history)
        current_count = detection_history[-1][1]
    else:
        avg_count, max_count, current_count = 0, 0, 0
    
    # 构造大模型提示词
    try:
        prompt = f"当前监控状态：当前检测到 {current_count} 人，最近 5 分钟平均人数 {avg_count:.1f}，峰值 {max_count} 人。请根据这些人流量数据给出一条专业的监控决策建议（20字以内）。"
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50
        )
        suggestion = response.choices[0].message.content.strip()
    except Exception as e:
        suggestion = "建议：保持监控，观察人员流动趋势。"
        
    # 构造返回数据
    result = {
        "suggestion": suggestion,
        "current_count": current_count,
        "avg_count": round(avg_count, 2),
        "max_count": max_count,
        "logs": list(detection_logs),
        "history": list(detection_history)
    }
    
    return jsonify(result)

def gen_display():
    global detection_history, detection_logs
    
    footage_socket = context.socket(zmq.SUB)
    footage_socket.connect('tcp://127.0.0.1:5555')
    footage_socket.setsockopt_string(zmq.SUBSCRIBE, '')
    footage_socket.RCVTIMEO = 2000 

    print("Flask Video Feed connected to ZMQ...")

    while True:
        try:
            # 接收格式：b"COUNT|DATA"
            message = footage_socket.recv()
            parts = message.split(b'|', 1)
            if len(parts) < 2: continue
            
            count = int(parts[0].decode())
            img_data = base64.b64decode(parts[1])
            
            # 更新历史数据
            timestamp = time.strftime("%H:%M:%S")
            detection_history.append((timestamp, count))
            
            # 如果人数发生变化，记录日志
            if len(detection_logs) == 0 or detection_logs[-1]['count'] != count:
                log_entry = {
                    "time": timestamp,
                    "count": count,
                    "msg": f"检测到 {count} 名人员"
                }
                detection_logs.append(log_entry)
            
            # 将数据直接发送给前端
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + img_data + b'\r\n')
            
        except zmq.Again:
            continue
        except Exception as e:
            print(f"Error in gen_display: {e}")
            break
    
    footage_socket.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
