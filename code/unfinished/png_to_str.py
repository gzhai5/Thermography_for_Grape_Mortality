import base64
import numpy as np

with open("test_png_file.png", "rb") as f:
    png_encoded = base64.b64encode(f.read())

encoded_b2 = "".join([format(n, '08b') for n in png_encoded])
# print(encoded_b2)
# print(type(encoded_b2))
# print(len(encoded_b2))
numpy_array1 = np.fromstring(encoded_b2, dtype=float)
print(numpy_array1)

text_file = open("data.txt", "w")
text_file.write(encoded_b2)
text_file.close


# decoded_b64 = b"".join([bytes(chr(int(encoded_b2[i:i+8], 2)), "utf-8") for i in range (0, len(encoded_b2), 8)])
# with open('my_image_decoded.png', 'wb') as f:
#     f.write(base64.b64decode(decoded_b64))
