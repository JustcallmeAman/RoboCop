"""
RoboCop Vision

Object detection via the OAK-D Lite's onboard MyriadX neural engine.
Runs entirely on the camera hardware — zero Jetson GPU/CPU cost.
"""

import depthai as dai
import time

from config import (
    DETECTION_MODEL, DETECTION_PLATFORM, DETECTION_CONFIDENCE,
    CAMERA_PREVIEW_SIZE, DETECTION_LABELS,
)

_pipeline = None
_queue = None


def init():
    """Build and start the detection pipeline on the OAK-D Lite."""
    global _pipeline, _queue

    print('Starting OAK-D Lite...')

    _pipeline = dai.Pipeline()

    cam = _pipeline.create(dai.node.Camera)
    cam.build()
    cam_out = cam.requestOutput(CAMERA_PREVIEW_SIZE, type=dai.ImgFrame.Type.BGR888p)

    nn = _pipeline.create(dai.node.DetectionNetwork)
    nn.setFromModelZoo(dai.NNModelDescription(
        model=DETECTION_MODEL, platform=DETECTION_PLATFORM
    ))
    nn.setConfidenceThreshold(DETECTION_CONFIDENCE)

    cam_out.link(nn.input)
    _queue = nn.out.createOutputQueue()

    _pipeline.start()
    print('OAK-D Lite ready.')


def get_detections():
    """Return a list of (label, confidence) tuples from the latest frame.

    Non-blocking — returns an empty list if no new frame is available.
    """
    data = _queue.tryGet()
    if not data:
        return []

    results = []
    for det in data.detections:
        label = DETECTION_LABELS[det.label] if det.label < len(DETECTION_LABELS) else f'class_{det.label}'
        results.append((label, det.confidence))
    return results


def describe_scene(duration=1.0):
    """Watch for `duration` seconds and return a summary string.

    Aggregates detections over multiple frames and returns a
    human-readable description like "I see 2 people and a chair".
    """
    seen = {}
    start = time.time()
    while time.time() - start < duration:
        for label, conf in get_detections():
            if label == 'background':
                continue
            if label not in seen or conf > seen[label]:
                seen[label] = conf
        time.sleep(0.05)

    if not seen:
        return None

    parts = []
    for label, conf in sorted(seen.items(), key=lambda x: -x[1]):
        parts.append(f'{label} ({conf:.0%})')
    return ', '.join(parts)


def stop():
    """Stop the camera pipeline."""
    global _pipeline, _queue
    if _pipeline:
        _pipeline.stop()
        _pipeline = None
        _queue = None
