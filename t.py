from PIL import Image
import os

source_folder = r'C:/Users/thanh/Downloads/images/'
destination_folder = r'C:/Users/thanh/Downloads/images/'

for item in os.listdir(source_folder):
    img = Image.open(source_folder + item)
    width, height = img.size
    ratio = width / height
    new_width = 640
    new_height = int(new_width/ratio)
    imgResize = img.resize((new_width, new_height), Image.ANTIALIAS)
    imgResize.save(destination_folder + item[:-4] + '.jpg', quality=100)