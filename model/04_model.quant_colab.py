# ============================================================================
# 🚀 1단계: 환경 설정 및 라이브러리 설치
# ============================================================================

print("🔧 Edge TPU 변환 환경 설정 중...")

# 필수 라이브러리 설치
!pip install ultralytics -q
!pip install tensorflow -q
!pip install pillow -q

print("✅ 라이브러리 설치 완료!")

# 필수 라이브러리 import
import os
import yaml
import shutil
import zipfile
from pathlib import Path
from google.colab import files as colab_files
from collections import defaultdict
import random
from PIL import Image
import time
from ultralytics import YOLO

print("✅ 필수 라이브러리 import 완료!")
print("🔄 다음 셀(2단계)을 실행하세요: 모델 파일 업로드")

# ============================================================================
# 🚀 2단계: 모델 파일 업로드
# ============================================================================

print("📁 YOLO 모델 파일(.pt) 업로드")
print("💡 지원 형식: .pt (PyTorch 모델)")
print("📏 권장 크기: 50MB 이하 (빠른 변환을 위해)")
print("-" * 50)

# 파일 업로드
uploaded_models = colab_files.upload()

if uploaded_models:
    model_filename = list(uploaded_models.keys())[0]
    print(f"\n✅ 모델 업로드 완료!")
    print(f"📁 파일명: {model_filename}")
    
    # 파일 존재 확인
    if os.path.exists(model_filename):
        print(f"✅ 파일 존재 확인됨")
    else:
        print(f"❌ 파일이 존재하지 않습니다!")
        exit()
    
    # 전역 변수로 저장
    globals()['model_filename'] = model_filename
    print(f"✅ 모델 파일 변수 저장 완료")
    
else:
    print("❌ 모델 파일이 업로드되지 않았습니다.")
    print("🔄 이 셀을 다시 실행해서 파일을 업로드하세요.")
    exit()

print(f"\n🔄 다음 셀(3단계)을 실행하세요: 모델 파일 검증")


# ============================================================================
# 🚀 3단계: 모델 파일 검증
# ============================================================================

print("🔍 업로드된 모델 파일 검증 중...")

# 변수 존재 확인
if 'model_filename' not in globals():
    print("❌ model_filename 변수가 없습니다!")
    print("🔄 2단계부터 다시 실행하세요.")
    exit()

print(f"📁 검증할 파일: {model_filename}")

# 파일 크기 확인
if os.path.exists(model_filename):
    size_bytes = os.path.getsize(model_filename)
    size_mb = size_bytes / (1024 * 1024)
    print(f"📏 파일 크기: {size_mb:.2f} MB")
    
    if size_mb > 100:
        print("⚠️ 파일이 큽니다. 변환 시간이 오래 걸릴 수 있습니다.")
    elif size_mb < 1:
        print("⚠️ 파일이 너무 작습니다. 올바른 모델 파일인지 확인하세요.")
    else:
        print("✅ 적절한 파일 크기입니다.")
else:
    print("❌ 파일이 존재하지 않습니다!")
    exit()

# 모델 로드 테스트
try:
    print("\n🔄 YOLO 모델 로드 테스트 중...")
    test_model = YOLO(model_filename)
    
    print("✅ 모델 로드 성공!")
    
    # 모델 정보 출력
    if hasattr(test_model, 'names') and test_model.names:
        print(f"📊 클래스 수: {len(test_model.names)}")
        print(f"📋 클래스 목록: {list(test_model.names.values())}")
        
        # 전역 변수로 저장
        globals()['model_classes'] = test_model.names
        globals()['num_classes'] = len(test_model.names)
    else:
        print("⚠️ 클래스 정보를 찾을 수 없습니다.")
        globals()['model_classes'] = {0: 'object'}
        globals()['num_classes'] = 1
    
    # 모델 타입 확인
    print(f"📱 모델 타입: {test_model.task}")
    
    # 입력 크기 정보
    if hasattr(test_model, 'model') and hasattr(test_model.model, 'yaml'):
        print("✅ 모델 구조 정보 확인됨")
    
    print("✅ 모델 검증 완료!")
    
except Exception as e:
    print(f"❌ 모델 로드 실패!")
    print(f"오류: {str(e)}")
    print("💡 올바른 YOLO .pt 파일인지 확인하세요.")
    exit()

print(f"\n🔄 다음 셀(4단계)을 실행하세요: Representative Dataset 옵션 선택")


# ============================================================================
# 🚀 4단계: Representative Dataset 옵션 선택
# ============================================================================

print("🎯 Representative Dataset 준비")
print("📋 Calibration용 이미지를 준비하는 방법을 선택하세요:")
print("")
print("1️⃣ 샘플 이미지 자동 생성 (빠른 테스트용)")
print("   • 100장의 랜덤 컬러 이미지 생성")
print("   • 빠른 테스트용 (품질: 보통)")
print("   • 변환 시간: 5분 내외")
print("")
print("2️⃣ 실제 데이터셋 ZIP 파일 업로드 (권장)")
print("   • 클래스별로 최대 10장씩 선별")
print("   • 높은 변환 품질")
print("   • 실제 도메인 데이터 사용")
print("")

choice = input("옵션을 선택하세요 (1 또는 2): ").strip()

# 선택 저장
globals()['dataset_choice'] = choice

# 기본 디렉토리 설정
dataset_dir = "/content/calibration_dataset"
os.makedirs(dataset_dir, exist_ok=True)
globals()['dataset_dir'] = dataset_dir

if choice == "1":
    print("✅ 옵션 1 선택: 샘플 이미지 자동 생성")
    print("🔄 다음 셀(5단계)을 실행하세요: 샘플 이미지 생성")
    
elif choice == "2":
    print("✅ 옵션 2 선택: 실제 데이터셋 ZIP 업로드")
    print("📋 ZIP 파일 구조 요구사항:")
    print("   📁 val/")
    print("   ├── 📁 images/")
    print("   │   ├── 🖼️ image1.jpg")
    print("   │   └── 🖼️ image2.jpg")
    print("   └── 📁 labels/")
    print("       ├── 📄 image1.txt")
    print("       └── 📄 image2.txt")
    print("")
    print("🔄 다음 셀(6단계)을 실행하세요: ZIP 파일 업로드")
    
else:
    print("❌ 잘못된 선택입니다. 1 또는 2를 입력하세요.")
    print("🔄 이 셀을 다시 실행하세요.")


    # ============================================================================
# 🚀 6단계: ZIP 파일 업로드 (옵션 2 선택시만 실행)
# ============================================================================

# 옵션 확인
if 'dataset_choice' not in globals() or dataset_choice != "2":
    print("⚠️ 이 셀은 옵션 2 선택시에만 실행하세요!")
    print("💡 옵션 1을 선택했다면 5단계로 이동하세요.")
    exit()

print("📦 YOLO 데이터셋 ZIP 파일 업로드")
print("📋 필수 구조:")
print("   📁 your_dataset.zip")
print("   └── 📁 val/")
print("       ├── 📁 images/ (jpg, png 파일들)")
print("       └── 📁 labels/ (txt 파일들)")
print("")
print("💡 팁:")
print("   • 클래스별로 다양한 이미지가 있을수록 좋습니다")
print("   • 각 클래스별 최대 10장씩 자동 선별됩니다")
print("   • 총 이미지 수가 많아도 괜찮습니다")

print("-" * 50)

# ZIP 파일 업로드
uploaded_zip = colab_files.upload()

if not uploaded_zip:
    print("❌ ZIP 파일이 업로드되지 않았습니다.")
    print("🔄 이 셀을 다시 실행해서 파일을 업로드하세요.")
    exit()

zip_filename = list(uploaded_zip.keys())[0]
print(f"\n✅ ZIP 파일 업로드 완료!")
print(f"📁 파일명: {zip_filename}")

# 파일 크기 확인
if os.path.exists(zip_filename):
    size_bytes = os.path.getsize(zip_filename)
    size_mb = size_bytes / (1024 * 1024)
    print(f"📏 파일 크기: {size_mb:.2f} MB")
    
    if size_mb > 500:
        print("⚠️ 파일이 큽니다. 압축 해제에 시간이 걸릴 수 있습니다.")
else:
    print("❌ 업로드된 파일이 존재하지 않습니다!")
    exit()

# 전역 변수로 저장
globals()['zip_filename'] = zip_filename

print(f"\n✅ ZIP 파일 업로드 완료!")
print(f"🔄 다음 셀(7단계)을 실행하세요: ZIP 압축 해제 및 구조 확인")


# ============================================================================
# 🚀 7단계: ZIP 압축 해제 및 구조 확인 (옵션 2 선택시만 실행)
# ============================================================================

# 변수 확인
if 'zip_filename' not in globals():
    print("❌ zip_filename 변수가 없습니다!")
    print("🔄 6단계부터 다시 실행하세요.")
    exit()

print(f"📦 ZIP 파일 압축 해제 시작: {zip_filename}")

try:
    # ZIP 압축 해제
    with zipfile.ZipFile(zip_filename, 'r') as zip_ref:
        zip_ref.extractall(dataset_dir)
    
    print(f"✅ 압축 해제 완료!")
    print(f"📁 해제 위치: {dataset_dir}")
    
except Exception as e:
    print(f"❌ 압축 해제 실패: {str(e)}")
    exit()

# 압축 해제 후 구조 탐색
print(f"\n🔍 폴더 구조 탐색 중...")

val_images_path = None
val_labels_path = None

# 1차 탐색: 정확한 구조 찾기
for root, dirs, files in os.walk(dataset_dir):
    current_folder = os.path.basename(root)
    parent_folder = os.path.basename(os.path.dirname(root))
    
    if current_folder == 'images' and ('val' in parent_folder or 'val' in root):
        val_images_path = root
        print(f"🎯 val/images 발견: {root}")
        
    elif current_folder == 'labels' and ('val' in parent_folder or 'val' in root):
        val_labels_path = root
        print(f"🎯 val/labels 발견: {root}")

# 2차 탐색: 백업 방법
if not val_images_path or not val_labels_path:
    print("🔍 백업 탐색 중...")
    
    for root, dirs, files in os.walk(dataset_dir):
        if 'val' in os.path.basename(root).lower():
            if 'images' in dirs and not val_images_path:
                val_images_path = os.path.join(root, 'images')
                print(f"🎯 val/images 발견 (백업): {val_images_path}")
                
            if 'labels' in dirs and not val_labels_path:
                val_labels_path = os.path.join(root, 'labels')
                print(f"🎯 val/labels 발견 (백업): {val_labels_path}")

# 구조 확인 결과
if val_images_path and val_labels_path:
    print(f"\n✅ 올바른 데이터셋 구조 발견!")
    
    # 파일 개수 확인
    image_files = [f for f in os.listdir(val_images_path) 
                   if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    label_files = [f for f in os.listdir(val_labels_path) 
                   if f.endswith('.txt')]
    
    print(f"📊 이미지 파일: {len(image_files)}개")
    print(f"📄 라벨 파일: {len(label_files)}개")
    
    if len(image_files) == 0:
        print("❌ 이미지 파일이 없습니다!")
        exit()
    
    if len(label_files) == 0:
        print("❌ 라벨 파일이 없습니다!")
        exit()
    
    # 전역 변수 저장
    globals()['val_images_path'] = val_images_path
    globals()['val_labels_path'] = val_labels_path
    
    print(f"\n✅ 데이터셋 구조 확인 완료!")
    print(f"🔄 다음 셀(8단계)을 실행하세요: 클래스별 이미지 분류 및 샘플링")
    
else:
    print(f"\n❌ 올바른 데이터셋 구조를 찾을 수 없습니다!")
    print(f"📋 현재 폴더 구조:")
    
    for root, dirs, files in os.walk(dataset_dir):
        level = root.replace(dataset_dir, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}📁 {os.path.basename(root)}/")
        
        subindent = ' ' * 2 * (level + 1)
        for file in files[:5]:  # 최대 5개 파일만 표시
            print(f"{subindent}📄 {file}")
        if len(files) > 5:
            print(f"{subindent}... 및 {len(files)-5}개 더")
    
    print(f"\n💡 필요한 구조:")
    print(f"   📁 val/")
    print(f"   ├── 📁 images/")
    print(f"   └── 📁 labels/")
    exit()


    # ============================================================================
# 🚀 8단계: 클래스별 이미지 분류 및 샘플링 (옵션 2 선택시만 실행)
# ============================================================================

# 변수 확인
required_vars = ['val_images_path', 'val_labels_path', 'dataset_dir']
missing_vars = [var for var in required_vars if var not in globals()]

if missing_vars:
    print(f"❌ 필수 변수가 없습니다: {missing_vars}")
    print("🔄 7단계부터 다시 실행하세요.")
    exit()

print("🎯 클래스별 이미지 분류 및 샘플링 시작!")
print(f"📁 이미지 경로: {val_images_path}")
print(f"📄 라벨 경로: {val_labels_path}")

# 클래스별 이미지 분류
class_images = defaultdict(list)
processed_count = 0
error_count = 0

label_files = [f for f in os.listdir(val_labels_path) if f.endswith('.txt')]
total_labels = len(label_files)

print(f"\n📄 라벨 파일 분석 중... (총 {total_labels}개)")

for i, label_file in enumerate(label_files):
    label_path = os.path.join(val_labels_path, label_file)
    image_base = label_file.replace('.txt', '')
    
    # 이미지 파일 찾기
    image_file = None
    for ext in ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']:
        test_image = image_base + ext
        if os.path.exists(os.path.join(val_images_path, test_image)):
            image_file = test_image
            break
    
    if not image_file:
        error_count += 1
        continue
    
    # 라벨에서 클래스 ID 추출
    try:
        with open(label_path, 'r') as f:
            content = f.read().strip()
            if content:
                lines = content.split('\n')
                for line in lines:
                    if line.strip():
                        class_id = int(line.split()[0])
                        class_images[class_id].append(image_file)
                        break  # 첫 번째 클래스만 사용
        processed_count += 1
        
    except Exception as e:
        error_count += 1
        continue
    
    # 진행률 표시
    if (i + 1) % 100 == 0 or (i + 1) == total_labels:
        print(f"   📊 진행률: {i + 1}/{total_labels} ({(i + 1)/total_labels*100:.1f}%)")

print(f"\n📊 분석 완료!")
print(f"✅ 처리된 파일: {processed_count}개")
print(f"❌ 오류 파일: {error_count}개")

# 중복 제거 및 클래스별 분포 출력
print(f"\n📊 클래스별 이미지 분포:")
for class_id in sorted(class_images.keys()):
    unique_images = list(set(class_images[class_id]))
    class_images[class_id] = unique_images
    print(f"   클래스 {class_id:2d}: {len(unique_images):4d}개")

if not class_images:
    print("❌ 분류된 이미지가 없습니다!")
    print("💡 라벨 파일 형식을 확인하세요.")
    exit()

# 클래스별 10장씩 샘플링
print(f"\n🎯 클래스별로 최대 10장씩 선택:")
selected_images = []

for class_id in sorted(class_images.keys()):
    available = class_images[class_id]
    random.shuffle(available)
    selected = available[:min(len(available), 10)]
    selected_images.extend(selected)
    print(f"   클래스 {class_id:2d}: {len(selected):2d}장 선택")

# 선별된 이미지 복사
sampled_dir = f"{dataset_dir}/sampled_images"
os.makedirs(sampled_dir, exist_ok=True)

print(f"\n📦 선별된 이미지 복사 중...")

for i, img_file in enumerate(selected_images):
    src = os.path.join(val_images_path, img_file)
    ext = os.path.splitext(img_file)[1]
    dst = os.path.join(sampled_dir, f"sample_{i:03d}{ext}")
    
    try:
        shutil.copy2(src, dst)
    except Exception as e:
        print(f"❌ 복사 실패 {img_file}: {str(e)}")
        continue
    
    # 진행률 표시
    if (i + 1) % 20 == 0 or (i + 1) == len(selected_images):
        print(f"   📊 복사 진행률: {i + 1}/{len(selected_images)} ({(i + 1)/len(selected_images)*100:.1f}%)")

# 변수 설정
image_count = len(selected_images)
relative_val_path = 'sampled_images'

# 전역 변수 저장
globals()['image_count'] = image_count
globals()['relative_val_path'] = relative_val_path

# 실제 복사된 파일 수 확인
actual_files = len([f for f in os.listdir(sampled_dir) 
                   if f.lower().endswith(('.jpg', '.jpeg', '.png'))])

print(f"\n🎉 클래스별 샘플링 완료!")
print(f"📊 선택된 이미지: {image_count}개")
print(f"📁 실제 복사된 파일: {actual_files}개")
print(f"📁 저장 경로: {relative_val_path}")

# 품질 등급 표시
if image_count >= 300:
    quality = "🟢 최고 품질"
elif image_count >= 100:
    quality = "🟡 양호한 품질"
elif image_count >= 50:
    quality = "🟠 보통 품질"
else:
    quality = "🔴 낮은 품질"

print(f"🎯 예상 품질: {quality}")
print(f"⏰ 예상 변환 시간: 5-10분")

print(f"\n🔄 다음 셀(9단계)을 실행하세요: data.yaml 생성")


# ============================================================================
# 🚀 9단계: data.yaml 생성
# ============================================================================

# 필수 변수 확인
required_vars = ['dataset_dir', 'image_count', 'relative_val_path']
missing_vars = [var for var in required_vars if var not in globals()]

if missing_vars:
    print(f"❌ 필수 변수가 없습니다: {missing_vars}")
    print("🔄 이전 단계부터 다시 실행하세요.")
    exit()

print("📄 data.yaml 파일 생성 중...")
print(f"📁 데이터셋 경로: {dataset_dir}")
print(f"📊 이미지 개수: {image_count}개")
print(f"📁 상대 경로: {relative_val_path}")

# 기본 클래스 정보 설정
if 'model_classes' in globals() and 'num_classes' in globals():
    # 모델에서 추출한 클래스 정보 사용
    nc = num_classes
    names = list(model_classes.values())
    print(f"✅ 모델에서 클래스 정보 추출:")
    print(f"   📊 클래스 수: {nc}")
    print(f"   📋 클래스명: {names}")
else:
    # 기본값 사용
    nc = 1
    names = ['object']
    print(f"⚠️ 모델 클래스 정보가 없어 기본값 사용:")
    print(f"   📊 클래스 수: {nc}")
    print(f"   📋 클래스명: {names}")

# data.yaml 내용 생성
yaml_content = {
    'path': dataset_dir,
    'train': relative_val_path,
    'val': relative_val_path,
    'nc': nc,
    'names': names
}

# YAML 파일 저장
yaml_path = f"{dataset_dir}/data.yaml"

try:
    with open(yaml_path, 'w') as f:
        yaml.dump(yaml_content, f, default_flow_style=False, allow_unicode=True)
    
    print(f"\n✅ data.yaml 생성 완료!")
    print(f"📁 파일 위치: {yaml_path}")
    
    # 전역 변수 저장
    globals()['yaml_path'] = yaml_path
    
except Exception as e:
    print(f"❌ YAML 파일 생성 실패: {str(e)}")
    exit()

# 생성된 YAML 내용 확인
try:
    with open(yaml_path, 'r') as f:
        saved_content = yaml.safe_load(f)
    
    print(f"\n📋 생성된 data.yaml 내용:")
    print(f"   path: {saved_content.get('path', 'N/A')}")
    print(f"   train: {saved_content.get('train', 'N/A')}")
    print(f"   val: {saved_content.get('val', 'N/A')}")
    print(f"   nc: {saved_content.get('nc', 'N/A')}")
    print(f"   names: {saved_content.get('names', 'N/A')}")
    
except Exception as e:
    print(f"⚠️ YAML 파일 읽기 실패: {str(e)}")

# 파일 존재 확인
if os.path.exists(yaml_path):
    file_size = os.path.getsize(yaml_path)
    print(f"✅ 파일 크기: {file_size} bytes")
    
    if file_size > 0:
        print(f"✅ data.yaml 파일이 정상적으로 생성되었습니다!")
    else:
        print(f"❌ 파일이 비어있습니다!")
        exit()
else:
    print(f"❌ 파일이 생성되지 않았습니다!")
    exit()

# Representative Dataset 경로 확인
rep_dataset_path = os.path.join(dataset_dir, relative_val_path)
if os.path.exists(rep_dataset_path):
    actual_images = len([f for f in os.listdir(rep_dataset_path) 
                        if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
    print(f"✅ Representative Dataset 확인: {actual_images}개 이미지")
    
    if actual_images != image_count:
        print(f"⚠️ 예상({image_count})과 실제({actual_images}) 이미지 수가 다릅니다.")
        # 실제 개수로 업데이트
        globals()['image_count'] = actual_images
else:
    print(f"❌ Representative Dataset 경로가 존재하지 않습니다: {rep_dataset_path}")
    exit()

print(f"\n🎯 Calibration 준비 완료!")
print(f"📊 최종 이미지 개수: {image_count}개")
print(f"📄 YAML 파일: {yaml_path}")

print(f"\n🔄 다음 셀(10단계)을 실행하세요: Edge TPU 변환 실행")


# ============================================================================
# 🚀 10단계: Edge TPU 변환 실행
# ============================================================================

# 필수 변수 확인
required_vars = ['model_filename', 'yaml_path', 'image_count']
missing_vars = [var for var in required_vars if var not in globals()]

if missing_vars:
    print(f"❌ 필수 변수가 없습니다: {missing_vars}")
    print("🔄 이전 단계부터 다시 실행하세요.")
    exit()

# 변환 전 최종 확인
print("🚀 Edge TPU 변환 최종 확인")
print("=" * 60)
print(f"📁 모델 파일: {os.path.basename(model_filename)}")
print(f"📄 Calibration 설정: {yaml_path}")
print(f"📊 Representative 이미지: {image_count}개")

# 파일 존재 확인
if not os.path.exists(model_filename):
    print(f"❌ 모델 파일이 존재하지 않습니다: {model_filename}")
    exit()

if not os.path.exists(yaml_path):
    print(f"❌ YAML 파일이 존재하지 않습니다: {yaml_path}")
    exit()

print("=" * 60)

# 변환 시작
try:
    print(f"\n🔄 YOLO 모델 로드 중...")
    model = YOLO(model_filename)
    print(f"✅ 모델 로드 성공!")
    
    # 모델 정보 출력
    if hasattr(model, 'names') and model.names:
        print(f"📊 모델 클래스 수: {len(model.names)}")
        print(f"📋 클래스 목록: {list(model.names.values())}")
        
        # YAML 파일의 클래스 정보 업데이트
        print(f"🔄 YAML 파일 클래스 정보 업데이트 중...")
        try:
            with open(yaml_path, 'r') as f:
                yaml_content = yaml.safe_load(f)
            
            yaml_content['nc'] = len(model.names)
            yaml_content['names'] = list(model.names.values())
            
            with open(yaml_path, 'w') as f:
                yaml.dump(yaml_content, f, default_flow_style=False, allow_unicode=True)
            
            print(f"✅ YAML 클래스 정보 업데이트 완료")
            
        except Exception as e:
            print(f"⚠️ YAML 업데이트 실패 (계속 진행): {str(e)}")
    
    # 변환 시작 시간 기록
    start_time = time.time()
    
    print(f"\n🔄 Edge TPU 변환 진행 중...")
    print("   📋 변환 단계:")
    print("   🔄 1단계: PyTorch → ONNX")
    print("   🔄 2단계: ONNX → TensorFlow")
    print("   🔄 3단계: TensorFlow → TFLite")
    print("   🔄 4단계: Representative dataset으로 INT8 calibration")
    print("   🔄 5단계: TFLite → Edge TPU")
    print("")
    print("   ⏳ 예상 소요 시간:")
    if image_count >= 200:
        print("      📊 많은 이미지: 10-15분")
    elif image_count >= 100:
        print("      📊 보통 이미지: 5-10분")
    else:
        print("      📊 적은 이미지: 3-7분")
    
    print("\n" + "⏳" * 20 + " 변환 중... " + "⏳" * 20)
    
    # Edge TPU 변환 실행
    export_path = model.export(
        format="edgetpu",
        imgsz=320,
        data=yaml_path,
        verbose=True
    )
    
    # 변환 완료 시간 계산
    conversion_time = time.time() - start_time
    minutes = int(conversion_time // 60)
    seconds = int(conversion_time % 60)
    
    print("\n" + "🎉" * 25)
    print("Edge TPU 변환 성공!")
    print("🎉" * 25)
    
    if export_path and os.path.exists(export_path):
        # 파일 정보
        size_bytes = os.path.getsize(export_path)
        size_mb = size_bytes / (1024 * 1024)
        
        print(f"\n📋 변환 결과:")
        print(f"✅ 출력 파일: {os.path.basename(export_path)}")
        print(f"📁 전체 경로: {export_path}")
        print(f"📏 파일 크기: {size_mb:.2f} MB")
        print(f"⏱️ 변환 시간: {minutes}분 {seconds}초")
        print(f"🎯 사용된 Calibration 이미지: {image_count}개")
        
        # 변환 품질 평가
        if image_count >= 300:
            quality = "🟢 최고 품질 (300+ 이미지)"
        elif image_count >= 100:
            quality = "🟡 양호한 품질 (100+ 이미지)"
        elif image_count >= 50:
            quality = "🟠 보통 품질 (50+ 이미지)"
        else:
            quality = "🔴 낮은 품질 (50개 미만)"
        
        print(f"📈 예상 양자화 품질: {quality}")
        
        # 전역 변수로 저장
        globals()['edge_tpu_model_path'] = export_path
        globals()['conversion_success'] = True
        
        print(f"\n🚀 성능 예상치:")
        print(f"   ⚡ 추론 속도: ~15-30ms (Coral Dev Board)")
        print(f"   🎯 정확도: 원본 모델 대비 90-95%")
        print(f"   💾 메모리 사용량: 원본 대비 1/4 감소")
        print(f"   🔋 전력 효율: GPU 대비 10배 향상")
        
        print(f"\n✅ 변환 완료!")
        print(f"🔄 다음 셀(11단계)을 실행하세요: 결과 다운로드")
        
    else:
        print("❌ 변환 실패: 출력 파일이 생성되지 않았습니다.")
        globals()['conversion_success'] = False
        
except Exception as e:
    print(f"\n💥 변환 오류 발생!")
    print("=" * 50)
    print(f"오류 내용: {str(e)}")
    print("=" * 50)
    
    print(f"\n💡 문제 해결 가이드:")
    print(f"1. 🔄 런타임 → 런타임 재시작 후 전체 다시 실행")
    print(f"2. 📊 이미지 크기 변경: imgsz=224 또는 imgsz=416 시도")
    print(f"3. 📁 더 적은 Representative 이미지 사용 (50개 정도)")
    print(f"4. 🎯 실제 도메인 이미지 대신 샘플 이미지 사용")
    print(f"5. 📱 다른 YOLO 모델 파일 시도")
    
    globals()['conversion_success'] = False
    
    # 상세 오류 정보
    import traceback
    print(f"\n🔍 상세 오류 정보:")
    print(traceback.format_exc())
    
    raise e