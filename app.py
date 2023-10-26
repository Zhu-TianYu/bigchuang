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
    footage_socket = context.socket(zmq.PAIR)
    footage_socket.bind('tcp://*:5555')

    while True:
        # print("监听中")
        frame = footage_socket.recv_string()  # 接收TCP传输过来的一帧视频图像数据
        img = base64.b64decode(frame)  # 把数据进行base64解码后储存到内存img变量中
        npimg = np.frombuffer(img, dtype=np.uint8)  # 把这段缓存解码成一维数组
        frame = cv2.imdecode(npimg, 3)  # 将一维数组解码为图像source
        ret, frame = cv2.imencode('.jpeg', frame)
        if ret:
            # 转换为byte类型的，存储在迭代器中
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame.tobytes() + b'\r\n')


if __name__ == '__main__':
    app.run()
