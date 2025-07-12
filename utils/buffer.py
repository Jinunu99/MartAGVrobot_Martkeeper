import queue

csi_frame = queue.Queue(maxsize=5)
usb_frame = queue.Queue(maxsize=5)