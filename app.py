from flask import Flask, Response, render_template
import cv2
import zmq
import base64
import numpy as np
import time

app = Flask(__name__)

# 全局复用 ZMQ Context
context = zmq.Context()

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/video_feed')
def video_feed():
    # 视频流相机对象
    return Response(gen_display(), mimetype='multipart/x-mixed-replace; boundary=frame')

def gen_display():
    # 创建订阅者 Socket
    footage_socket = context.socket(zmq.SUB)
    # 增加连接等待时间，确保能够连接到发布端
    footage_socket.connect('tcp://127.0.0.1:5555')
    footage_socket.setsockopt_string(zmq.SUBSCRIBE, '')
    # 设置接收超时，避免生成器永久阻塞
    footage_socket.RCVTIMEO = 2000 

    print("Video feed generator started, connecting to ZMQ...")

    while True:
        try:
            # 接收一帧数据
            frame_str = footage_socket.recv_string()
            
            # 数据解码
            img_data = base64.b64decode(frame_str)
            npimg = np.frombuffer(img_data, dtype=np.uint8)
            frame = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
            
            if frame is None:
                continue
                
            # 图像编码为 JPEG
            ret, frame_encoded = cv2.imencode('.jpg', frame)
            if ret:
                # 按照 MJPEG 格式 yield 数据
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_encoded.tobytes() + b'\r\n')
            
        except zmq.Again:
            # 超时未收到数据，打印日志但不退出
            # print("ZMQ Receive Timeout: No data from sender.")
            continue
        except Exception as e:
            print(f"Error in gen_display: {e}")
            break
    
    footage_socket.close()

if __name__ == '__main__':
    # 开启 threaded=True 以处理多个并发请求
    app.run(host='0.0.0.0', port=5000, threaded=True)
