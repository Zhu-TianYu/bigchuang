import zmq
import base64
import cv2
import time
import numpy as np

def send_video():
    context = zmq.Context()
    # 使用 PUB/SUB 模式，发布者绑定端口
    footage_socket = context.socket(zmq.PUB)
    footage_socket.bind('tcp://*:5555')
    
    # 视频分辨率设置
    width, height = 640, 480
    x = 0
    
    print("ZMQ Publisher started on port 5555. Sending mock video data...")
    # 稍微等待，让订阅者（Flask）有时间连接
    time.sleep(2)
    
    try:
        while True:
            # 创建带有移动圆圈的背景，背景颜色循环变化
            bg_color = (int(time.time() * 10) % 255, 100, 200)
            frame = np.full((height, width, 3), bg_color, dtype=np.uint8)
            
            # 画一个圆，圆的位置随时间变化
            cv2.circle(frame, (x % width, height // 2), 60, (0, 255, 0), -1)
            # 添加一些动态文字，确保截图能看出实时性
            cv2.putText(frame, f"LIVE: {time.strftime('%H:%M:%S')}", (50, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            x += 15
            
            # 图像编码
            ret, buffer = cv2.imencode('.jpg', frame)
            if ret:
                # 转换为 base64 字符串
                jpg_as_text = base64.b64encode(buffer)
                # 发送字符串
                footage_socket.send(jpg_as_text)
            
            # 控制帧率约为 20 FPS
            time.sleep(0.05)
            
    except KeyboardInterrupt:
        print("Stopping sender...")
    finally:
        footage_socket.close()
        context.term()

if __name__ == "__main__":
    send_video()
