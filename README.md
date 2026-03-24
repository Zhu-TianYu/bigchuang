# bigchuang - 基于 Flask 和 OpenCV 的实时视频流项目

## 1. 项目简介

`bigchuang` 是一个基于 Python Flask 框架和 OpenCV 库实现的实时视频流项目。它通过 ZeroMQ (ZMQ) 进行视频帧的传输，并在网页上展示。该项目旨在提供一个基础的视频监控或实时图像处理的 Web 界面。

## 2. 功能特性

*   **实时视频流**：通过网页实时显示视频画面。
*   **模块化设计**：Flask 负责 Web 服务，ZMQ 负责高效数据传输。
*   **易于扩展**：可在此基础上集成更多图像处理功能。

## 3. 环境要求

### 3.1 操作系统

*   **推荐**：Ubuntu 20.04+ 或其他 Linux 发行版。
*   **支持**：Windows (可能需要注意 OpenCV 摄像头驱动兼容性)。

### 3.2 Python 版本

*   Python 3.8 及以上版本。

### 3.3 Python 依赖

项目所需的所有 Python 依赖都列在 `requirements.txt` 文件中。您可以使用 `pip` 进行安装：

```bash
pip install -r requirements.txt
```

具体依赖包括：
*   `Flask`：Web 框架。
*   `opencv-python`：OpenCV 库的 Python 绑定，用于视频处理。
*   `pyzmq`：ZeroMQ 消息队列的 Python 绑定，用于帧传输。
*   `numpy`：用于处理图像数据。

## 4. 硬件设备

*   **摄像头**：一个可用的 USB 摄像头或 IP 摄像头（如果使用 IP 摄像头，需要修改 `app.py` 中的 `cv2.VideoCapture()` 参数）。
*   **计算资源**：由于涉及视频处理和传输，建议使用性能较好的 CPU 和足够的内存。

## 5. 安装与启动

请按照以下步骤安装和启动项目：

### 5.1 克隆仓库

首先，将项目仓库克隆到本地：

```bash
git clone https://github.com/Zhu-TianYu/bigchuang.git
cd bigchuang
```

### 5.2 安装依赖

进入项目目录后，安装所有必要的 Python 依赖：

```bash
pip install -r requirements.txt
```

### 5.3 启动 Flask 应用

在项目根目录下运行 `app.py` 启动 Flask Web 服务。这将启动一个在 `http://0.0.0.0:5000` 监听的服务器：

```bash
python3 app.py
```

### 5.4 启动视频流发送端

`app.py` 中的 `video_feed` 路由会尝试从 ZMQ 端口 `5555` 接收视频帧。您需要一个独立的程序来发送视频帧。本项目提供了一个 `mock_sender.py` 脚本用于模拟发送视频流：

```bash
python3 mock_sender.py
```

如果您有真实的摄像头，并且希望使用它作为视频源，您需要修改 `mock_sender.py` 或编写一个新的发送端脚本来从摄像头捕获帧并发送。

### 5.5 访问视频流

在 Flask 应用和视频流发送端都成功启动后，您可以通过浏览器访问以下地址查看实时视频流：

```
http://localhost:5000/
```

## 6. 初次使用配置

### 6.1 ZMQ 端口配置

`app.py` 和 `mock_sender.py` (或您的自定义发送端) 之间通过 ZMQ 进行通信。默认端口为 `5555`。

*   在 `app.py` 中，`footage_socket.bind("tcp://*:5555")` 表示 Flask 应用在 `5555` 端口上等待连接。
*   在 `mock_sender.py` 中，`footage_socket.connect("tcp://localhost:5555")` 表示发送端连接到 `localhost` 的 `5555` 端口。

如果您需要更改端口，请确保 `app.py` 和发送端脚本中的端口号保持一致。

### 6.2 摄像头配置

`app.py` 中的 `gen_display` 函数默认从 ZMQ 接收数据。如果您想直接在 `app.py` 中使用本地摄像头（不通过 ZMQ 发送端），您需要修改 `gen_display` 函数，取消注释并配置 `cv2.VideoCapture()`：

```python
def gen_display():
    camera = cv2.VideoCapture(0) # 0 通常代表默认摄像头，可以尝试 1, 2 等
    if not camera.isOpened():
        print("Error: Could not open video device.")
        return
    while True:
        ret, frame = camera.read()
        if not ret:
            break
        # ... 后续编码和 yield 逻辑 ...
```

**注意**：如果直接在 `app.py` 中使用摄像头，则不需要运行 `mock_sender.py`。

## 7. 项目结构

```
bigchuang/
├── app.py                  # Flask 主应用文件，处理 Web 请求和视频流接收
├── mock_sender.py          # 模拟视频流发送端，用于测试
├── requirements.txt        # Python 依赖列表
├── templates/              # HTML 模板文件
│   └── index.html          # 视频流显示页面
├── static/                 # 静态资源文件 (CSS, JS, 图片等)
└── modules/                # 其他模块 (如果存在)
```

## 8. 故障排除

*   **`ModuleNotFoundError`**：确保所有依赖都已通过 `pip install -r requirements.txt` 安装。
*   **端口占用**：如果 Flask 启动失败并提示端口 `5000` 被占用，请检查是否有其他程序正在使用该端口，或者修改 `app.py` 中的 `app.run(port=...)` 来使用其他端口。
*   **视频流无画面**：
    *   确保 `app.py` 和视频流发送端（如 `mock_sender.py`）都已成功启动。
    *   检查 ZMQ 端口配置是否一致。
    *   如果使用真实摄像头，请确保摄像头驱动正常，并且 `cv2.VideoCapture()` 参数正确。
*   **`zmq.Again` 错误**：这通常表示 ZMQ 接收端在设定的超时时间内没有收到消息。请确保发送端正在正常发送数据。

## 9. 许可证

[在此处添加您的许可证信息，例如 MIT License 或 Apache License 2.0]
