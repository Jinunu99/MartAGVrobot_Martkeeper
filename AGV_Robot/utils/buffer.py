import queue

csi_frame = queue.Queue(maxsize=5)
usb_frame = queue.Queue(maxsize=5)

rx_queue = queue.Queue(maxsize=5)
tx_queue = queue.Queue()  # 무제한

qr_result = queue.Queue(maxsize=5)     
line_trace_state = queue.Queue(maxsize=5)