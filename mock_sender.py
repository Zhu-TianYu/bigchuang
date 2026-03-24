import zmq
import base64
import cv2
import time
import numpy as np
import random
import os

def draw_realistic_face(frame, x, y):
    """
    在指定位置绘制具有人脸特征的几何图形，确保 Haar Cascade 能够识别
    """
    # 脸部轮廓 (椭圆)
    cv2.ellipse(frame, (x + 50, y + 60), (40, 50), 0, 0, 360, (200, 200, 200), -1)
    
    # 眼睛 (Haar Cascade 识别的关键特征)
    cv2.circle(frame, (x + 35, y + 45), 6, (255, 255, 255), -1) # 左眼白
    cv2.circle(frame, (x + 35, y + 45), 3, (0, 0, 0), -1)       # 左瞳孔
    cv2.circle(frame, (x + 65, y + 45), 6, (255, 255, 255), -1) # 右眼白
    cv2.circle(frame, (x + 65, y + 45), 3, (0, 0, 0), -1)       # 右瞳孔
    
    # 眉毛
    cv2.line(frame, (x + 25, y + 35), (x + 45, y + 35), (50, 50, 50), 2)
    cv2.line(frame, (x + 55, y + 35), (x + 75, y + 35), (50, 50, 50), 2)

    # 鼻子
    pts = np.array([[x + 50, y + 50], [x + 45, y + 70], [x + 55, y + 70]], np.int32)
    cv2.fillPoly(frame, [pts], (150, 150, 150))
    
    # 嘴巴
    cv2.ellipse(frame, (x + 50, y + 85), (15, 8), 0, 0, 180, (100, 100, 100), 2)

def send_video():
    context = zmq.Context()
    footage_socket = context.socket(zmq.PUB)
    footage_socket.bind('tcp://*:5555')
    
    width, height = 640, 480
    
    # 加载 OpenCV 内置的 Haar Cascade 人脸检测模型
    cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    face_cascade = cv2.CascadeClassifier(cascade_path)
    
    if face_cascade.empty():
        print(f"Error: Could not load face cascade from {cascade_path}")
        return

    # 初始化随机移动的“人脸”
    faces = []
    for _ in range(2):
        faces.append({
            'x': random.randint(50, width-150),
            'y': random.randint(50, height-150),
            'vx': random.uniform(2, 5) * random.choice([-1, 1]),
            'vy': random.uniform(-1, 1)
        })
    
    print("ZMQ Real Face Detection Sender started. Detecting and sending...")
    
    try:
        while True:
            # 1. 创建原始画面
            frame = np.full((height, width, 3), (30, 30, 30), dtype=np.uint8)
            
            # 绘制科技感背景网格
            for i in range(0, width, 80):
                cv2.line(frame, (i, 0), (i, height), (50, 50, 50), 1)
            for i in range(0, height, 80):
                cv2.line(frame, (0, i), (width, i), (50, 50, 50), 1)

            # 绘制移动的“真实人脸”特征
            for f in faces:
                f['x'] += f['vx']
                f['y'] += f['vy']
                if f['x'] < 0 or f['x'] > width - 100: f['vx'] *= -1
                if f['y'] < 0 or f['y'] > height - 120: f['vy'] *= -1
                draw_realistic_face(frame, int(f['x']), int(f['y']))

            # 2. 运行真实的人脸检测算法 (OpenCV Haar Cascade)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            detected_faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
            
            face_count = len(detected_faces)
            
            # 在画面上绘制检测到的结果
            for (x, y, w, h) in detected_faces:
                # 绘制蓝色识别框 (科技感)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 100, 0), 2)
                # 绘制四个角点增强科技感
                length = 15
                cv2.line(frame, (x, y), (x + length, y), (0, 255, 136), 3)
                cv2.line(frame, (x, y), (x, y + length), (0, 255, 136), 3)
                cv2.line(frame, (x+w, y), (x+w-length, y), (0, 255, 136), 3)
                cv2.line(frame, (x+w, y), (x+w, y+length), (0, 255, 136), 3)
                
                cv2.putText(frame, "ID: FACE_DETECTED", (x, y - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 136), 1)

            # 添加 HUD 信息
            cv2.putText(frame, f"FACES DETECTED: {face_count}", (20, 40), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 136), 2)
            cv2.putText(frame, "ALGORITHM: HAAR_CASCADE", (20, 70), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 255), 1)
            cv2.putText(frame, time.strftime("%Y-%m-%d %H:%M:%S"), (20, height-20), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 136), 1)

            # 3. 编码并发送
            ret, buffer = cv2.imencode('.jpg', frame)
            if ret:
                jpg_as_text = base64.b64encode(buffer)
                message = f"{face_count}|".encode() + jpg_as_text
                footage_socket.send(message)
            
            # 随机增减人脸数量
            if random.random() < 0.01:
                if len(faces) < 4:
                    faces.append({'x': random.randint(50, width-150), 'y': random.randint(50, height-150),
                                 'vx': random.uniform(2, 5) * random.choice([-1, 1]), 'vy': random.uniform(-1, 1)})
                elif len(faces) > 1:
                    faces.pop(0)

            time.sleep(0.04) # ~25 FPS
            
    except KeyboardInterrupt:
        print("Stopping sender...")
    finally:
        footage_socket.close()
        context.term()

if __name__ == "__main__":
    send_video()
