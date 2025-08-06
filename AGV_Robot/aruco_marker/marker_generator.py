import cv2
import cv2.aruco as aruco
import os
import numpy as np

def generate_aruco_markers(output_dir="aruco_markers", dictionary_id=aruco.DICT_5X5_100, marker_size=200, num_markers=10):
    """
    ArUco 마커 이미지를 생성하는 함수

    Parameters:
    - output_dir: 생성된 마커 이미지 저장 폴더
    - dictionary_id: 사용할 딕셔너리 (패턴 규칙 : aruco.DICT_4X4_50)
    - marker_size: 마커 이미지의 한 변 크기 (픽셀)
    - num_markers: 생성할 마커 개수
    """
    # aruco_marker 폴더 안에 aruco_markers 폴더 경로를 생성
    if output_dir is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(script_dir, "aruco_markers")
    else:
        # 사용자가 직접 입력한 경로도 상대경로로 자동 변환
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(script_dir, output_dir)
	
	# 딕셔너리 선택
    aruco_dict = aruco.getPredefinedDictionary(dictionary_id)

    # 출력 디렉토리 생성
    os.makedirs(output_dir, exist_ok=True)

    for i in range(1, num_markers + 1):
        # 마커 생성 (수정된 부분)
        img = aruco.generateImageMarker(aruco_dict, i, marker_size)
        file_path = os.path.join(output_dir, f"aruco_{i:03}.png")
        cv2.imwrite(file_path, img)
        print(f"✅ Saved: {file_path}")

# python -m aruco_marker.marker_generator
if __name__ == "__main__":
    generate_aruco_markers(
        output_dir="aruco_markers",
        dictionary_id=aruco.DICT_5X5_100,
        marker_size=300,
        num_markers=32
    )