import qrcode

for i in range(1, 11):  # ID:001 ~ ID:010
    qr_data = f"ID:{i:03}"
    img = qrcode.make(qr_data)
    img.save(f"qr_{i:03}.png")

print("QR 코드 생성 완료 ✅")