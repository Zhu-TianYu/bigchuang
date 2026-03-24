import zmq
import base64
import cv2
import time
import numpy as np

def send_video():
    context = zmq.Context()
    footage_socket = context.socket(zmq.PUB)
    # 绑定到端口而不是连接
    footage_socket.bind('tcp://*:5555')
    
    # 创建一个简单的图像（例如，一个移动的圆圈）
    width, height = 640, 480
    x = 0
    
    print("开始模拟发送视频流...")
    time.sleep(1)  # 给订阅者时间连接
    
    try:
        while True:
            # 创建黑色背景
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            # 画一个圆
            cv2.circle(frame, (x % width, height // 2), 50, (0, 255, 0), -1)
            x += 10
            
            # 编码并发送
            _, buffer = cv2.imencode('.jpeg', frame)
            jpg_as_text = base64.b64encode(buffer)
            footage_socket.send(jpg_as_text)
            
            time.sleep(0.05)  # 20 FPS
    except KeyboardInterrupt:
        print("停止发送。")

if __name__ == "__main__":
    send_video()
