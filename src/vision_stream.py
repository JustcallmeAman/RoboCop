"""
RoboCop Vision Stream

Live MJPEG stream from the OAK-D Lite with detection bounding boxes.
View at http://<jetson-ip>:8080 from any browser on the same network.
"""

import depthai as dai
import cv2
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

from config import (
    DETECTION_ARCHIVE_PATH, DETECTION_CONFIDENCE,
    CAMERA_PREVIEW_SIZE, DETECTION_LABELS,
)

STREAM_PORT = 8080
DISPLAY_SIZE = (480, 480)

_latest_frame = None
_frame_lock = threading.Lock()

COLORS = [
    (0, 255, 0), (255, 0, 0), (0, 0, 255), (255, 255, 0),
    (255, 0, 255), (0, 255, 255), (128, 255, 0), (255, 128, 0),
]


def _camera_loop():
    """Run the detection pipeline and update the latest frame."""
    global _latest_frame

    pipeline = dai.Pipeline()

    cam = pipeline.create(dai.node.Camera)
    cam.build()

    # Two separate outputs from the camera: one for display, one for NN
    rgb_out = cam.requestOutput(CAMERA_PREVIEW_SIZE, type=dai.ImgFrame.Type.BGR888p)
    nn_out = cam.requestOutput(CAMERA_PREVIEW_SIZE, type=dai.ImgFrame.Type.BGR888p)

    nn = pipeline.create(dai.node.DetectionNetwork)
    nn.setNNArchive(dai.NNArchive(DETECTION_ARCHIVE_PATH))
    nn.setConfidenceThreshold(DETECTION_CONFIDENCE)

    nn_out.link(nn.input)

    rgb_queue = rgb_out.createOutputQueue(maxSize=2, blocking=False)
    det_queue = nn.out.createOutputQueue(maxSize=2, blocking=False)

    pipeline.start()
    print('Camera pipeline started.')

    latest_dets = []

    while True:
        det_msg = det_queue.tryGet()
        if det_msg is not None:
            latest_dets = det_msg.detections

        frame_msg = rgb_queue.get()
        frame = frame_msg.getCvFrame()

        h, w = frame.shape[:2]
        for det in latest_dets:
            label_idx = det.label
            label = DETECTION_LABELS[label_idx] if label_idx < len(DETECTION_LABELS) else f'class_{label_idx}'
            if label == 'background':
                continue
            color = COLORS[label_idx % len(COLORS)]

            x1 = int(det.xmin * w)
            y1 = int(det.ymin * h)
            x2 = int(det.xmax * w)
            y2 = int(det.ymax * h)

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            text = f'{label} {det.confidence:.0%}'
            cv2.putText(frame, text, (x1, y1 - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        frame = cv2.resize(frame, DISPLAY_SIZE)
        with _frame_lock:
            _latest_frame = frame


class StreamHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<html><body style="margin:0;background:#000">'
                             b'<img src="/stream" style="width:100%;height:100vh;object-fit:contain">'
                             b'</body></html>')
        elif self.path == '/stream':
            self.send_response(200)
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=frame')
            self.end_headers()
            while True:
                with _frame_lock:
                    frame = _latest_frame
                if frame is None:
                    time.sleep(0.05)
                    continue
                _, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                try:
                    self.wfile.write(b'--frame\r\n')
                    self.wfile.write(b'Content-Type: image/jpeg\r\n\r\n')
                    self.wfile.write(jpeg.tobytes())
                    self.wfile.write(b'\r\n')
                except BrokenPipeError:
                    break
                time.sleep(0.033)
        elif self.path == '/snapshot':
            with _frame_lock:
                frame = _latest_frame
            if frame is None:
                self.send_error(503, 'No frame yet')
                return
            _, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            self.send_response(200)
            self.send_header('Content-Type', 'image/jpeg')
            self.end_headers()
            self.wfile.write(jpeg.tobytes())
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        pass


def main():
    cam_thread = threading.Thread(target=_camera_loop, daemon=True)
    cam_thread.start()

    print(f'Vision stream at http://0.0.0.0:{STREAM_PORT}')
    print(f'  Live:     http://0.0.0.0:{STREAM_PORT}/')
    print(f'  Snapshot: http://0.0.0.0:{STREAM_PORT}/snapshot')
    server = HTTPServer(('0.0.0.0', STREAM_PORT), StreamHandler)
    server.serve_forever()


if __name__ == '__main__':
    main()
