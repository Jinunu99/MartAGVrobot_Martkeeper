import qrcode

for i in range(1, 33):  # ID:001 ~ ID:010
    qr_data = f"ID:{i:03}"
    img = qrcode.make(qr_data)
    img.save(f"./qr_image/qr_{i:03}.png")

print("QR 코드 생성 완료 ✅")

# import qrcode

# # 1~10번 ID에 대응되는 좌표값을 미리 정의
# # 예시: ID 1 → (0,0), ID 2 → (1,0), … ID 10 → (3,3)
# coords = {
#     1: (0, 0),
#     2: (1, 0),
#     3: (2, 0),
#     4: (0, 1),
#     5: (1, 1),
#     6: (2, 1),
#     7: (0, 2),
#     8: (1, 2),
#     9: (2, 2),
#     10: (3, 3),
# }

# for i in range(1, 11):  # ID:001 ~ ID:010
#     x, y = coords[i]
#     qr_data = f"ID:{i:03},X:{x},Y:{y}"
#     img = qrcode.make(qr_data)
#     img.save(f"./qr_image/qr_test_{i:03}.png")
#     print(f"qr_{i:03}.png ▶ {qr_data}")

# print("QR 코드 생성 완료 ✅")
