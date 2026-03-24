from flask import Flask, Response, render_template
import cv2
import zmq
import base64
import numpy as np

app = Flask(__name__)


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/video_feed')
def video_feed():
    # 视频流相机对象
    return Response(gen_display(), mimetype='multipart/x-mixed-replace; boundary=frame')


def gen_display():
    # 加上cv2.CAP_DSHOW可以加快打开usb摄像头速度，只有win可以使用
    # camera = cv2.VideoCapture(1, cv2.CAP_DSHOW)

    context = zmq.Context()
    footage_socket = context.socket(zmq.SUB)
    footage_socket.bind('tcp://*:5555')
    footage_socket.setsockopt_string(zmq.SUBSCRIBE, '')
    footage_socket.RCVTIMEO = 1000  # 设置接收超时为 1000ms

    while True:
        try:
            # print("监听中")
            frame_str = footage_socket.recv_string()  # 接收TCP传输过来的一帧视频图像数据
            img = base64.b64decode(frame_str)  # 把数据进行base64解码后储存到内存img变量中
            npimg = np.frombuffer(img, dtype=np.uint8)  # 把这段缓存解码成一维数组
            frame = cv2.imdecode(npimg, 3)  # 将一维数组解码为图像source
            
            if frame is None:
                continue
                
            ret, frame_encoded = cv2.imencode('.jpeg', frame)
            if ret:
                # 转换为byte类型的，存储在迭代器中
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_encoded.tobytes() + b'\r\n')
        except zmq.Again:
            # 超时，继续循环
            continue
        except Exception as e:
            print(f"Error processing frame: {e}")
            continue


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
