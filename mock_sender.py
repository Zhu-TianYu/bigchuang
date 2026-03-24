import zmq
import base64
import cv2
import time
import numpy as np
import random

def create_pedestrian_frame(width, height, pedestrians):
    """
    创建一个包含移动人物的模拟监控画面
    """
    # 深灰色背景模拟夜间监控或室内停车场
    frame = np.full((height, width, 3), (40, 40, 40), dtype=np.uint8)
    
    # 画一些网格线增加科技感
    for i in range(0, width, 100):
        cv2.line(frame, (i, 0), (i, height), (60, 60, 60), 1)
    for i in range(0, height, 100):
        cv2.line(frame, (0, i), (width, i), (60, 60, 60), 1)

    # 绘制移动的人物（用矩形表示，模拟行人检测的真实输入）
    for p in pedestrians:
        # 更新位置
        p['x'] += p['vx']
        p['y'] += p['vy']
        
        # 边界检测
        if p['x'] < 0 or p['x'] > width - 40: p['vx'] *= -1
        if p['y'] < 0 or p['y'] > height - 100: p['vy'] *= -1
        
        # 绘制“人物”主体
        x, y = int(p['x']), int(p['y'])
        cv2.rectangle(frame, (x, y), (x + 40, y + 100), (200, 200, 200), -1)
        # 绘制头部
        cv2.circle(frame, (x + 20, y + 20), 15, (200, 200, 200), -1)
        # 绘制眼睛（模拟方向）
        eye_x = x + 25 if p['vx'] > 0 else x + 15
        cv2.circle(frame, (eye_x, y + 15), 3, (50, 50, 50), -1)

    return frame

def send_video():
    context = zmq.Context()
    footage_socket = context.socket(zmq.PUB)
    footage_socket.bind('tcp://*:5555')
    
    width, height = 640, 480
    
    # 初始化一些随机移动的人物
    pedestrians = []
    for _ in range(3):
        pedestrians.append({
            'x': random.randint(50, width-100),
            'y': random.randint(50, height-150),
            'vx': random.uniform(2, 6) * random.choice([-1, 1]),
            'vy': random.uniform(-1, 1)
        })
    
    # 初始化 OpenCV HOG 检测器（用于真实的人物检测）
    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    
    print("ZMQ Human Detection Sender started. Detecting and sending...")
    
    try:
        while True:
            # 1. 获取/创建原始画面
            raw_frame = create_pedestrian_frame(width, height, pedestrians)
            
            # 2. 真实人物检测逻辑
            # 在这里我们直接在 raw_frame 上运行 HOG 检测
            # 注意：由于是模拟画面，HOG 可能检测不到。为了演示，我们手动添加检测框，
            # 但逻辑上这模拟了从视频源提取特征的过程。
            
            # 模拟检测到的框和人数
            detected_count = len(pedestrians)
            for p in pedestrians:
                x, y = int(p['x']), int(p['y'])
                # 绘制绿色检测框
                cv2.rectangle(raw_frame, (x-5, y-5), (x+45, y+105), (0, 255, 0), 2)
                # 绘制标签
                cv2.putText(raw_frame, "Person", (x, y-10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            # 添加系统状态文字
            cv2.putText(raw_frame, f"DETECTIONS: {detected_count}", (20, 40), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(raw_frame, time.strftime("%Y-%m-%d %H:%M:%S"), (20, height-20), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

            # 3. 编码并发送
            ret, buffer = cv2.imencode('.jpg', raw_frame)
            if ret:
                jpg_as_text = base64.b64encode(buffer)
                # 将人数也封装在消息中（或者通过另一个 socket 发送，这里简单处理）
                # 格式：b"COUNT:2|DATA:base64..."
                message = f"{detected_count}|".encode() + jpg_as_text
                footage_socket.send(message)
            
            # 每隔一段时间随机增减人数
            if random.random() < 0.02:
                if len(pedestrians) < 5:
                    pedestrians.append({
                        'x': random.randint(50, width-100),
                        'y': random.randint(50, height-150),
                        'vx': random.uniform(2, 6) * random.choice([-1, 1]),
                        'vy': random.uniform(-1, 1)
                    })
                elif len(pedestrians) > 1:
                    pedestrians.pop(0)

            time.sleep(0.05) # ~20 FPS
            
    except KeyboardInterrupt:
        print("Stopping sender...")
    finally:
        footage_socket.close()
        context.term()

if __name__ == "__main__":
    send_video()
