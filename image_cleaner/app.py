import os
import base64
from flask import Flask, render_template, request,redirect
import concurrent
import concurrent.futures
from PIL import Image
from io import BytesIO
import threading
from image_cleaner.filesystems import LocalFileSystem, GoogleDriveFileSystem
from cachetools import TTLCache
tfolder = os.path.join(os.path.dirname(__file__), 'templates')

app = Flask(__name__,template_folder=tfolder)

BATCH_SIZE = 100
global all_images
global deleted_images
global cached_images
global filter_str
global batch_number
filter_str = ""
deleted_images=[]
all_images=[]
cached_images=TTLCache(maxsize=1000, ttl=60*5)

fs  = GoogleDriveFileSystem()#LocalFileSystem('/Users/csommeregger/Library/CloudStorage/GoogleDrive-christian.sommeregger@gmail.com/My Drive/lola/scrapes/')

def encode_image(image_path):
    global cached_images
    if cached_images.get(image_path) is not None:
        return cached_images[image_path]
    with fs.open(image_path, "rb") as f:
        image = Image.open(f)
        image = image.resize((300, 300))
        with BytesIO() as buffer:
            image.save(buffer, format="JPEG")
            encoded_image = base64.b64encode(buffer.getvalue()).decode("utf-8")
    cached_images[image_path] = encoded_image
    return encoded_image
def encode_batch(image_paths_list):

    print(f"encode_batch() requested {len(image_paths_list)} images")
    with concurrent.futures.ThreadPoolExecutor() as executor:
        encoded_images = list(executor.map(encode_image, image_paths_list))

    print(f"encoded {len(encoded_images)} images from {len(image_paths_list)} paths")
    return encoded_images

def init_images():
    print(tfolder)
    global all_images
    print("init images")
    for root, _, files in fs.walk():
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                all_images.append(fs.relpath(root,file))
    print(f"found {len(all_images)} images in total")

def get_image_batch(batch_number,filter_str,function="regular call"):
    global all_images
    start_idx = batch_number * BATCH_SIZE
    end_idx = start_idx + BATCH_SIZE
    if end_idx>len(all_images):
        end_idx = len(all_images)
    print(filter_str)
    print(len(all_images))
    print(len([img for img in all_images if filter_str in img]))
    rel_images = [img for img in [img for img in all_images if filter_str in img][start_idx:end_idx] if img not in deleted_images]
    encoded_batch = encode_batch(rel_images)
    print(f"return {len(encoded_batch)} images and {len(rel_images)} paths images: {function}")
    return encoded_batch,rel_images

def preload(batch_number,steps=3):
    for i in range(steps):
        thread  = threading.Thread(target=get_image_batch, args=(batch_number + i,"cache"))
        thread.start()

@app.route('/filter')
def filter():
    global filter_str
    global batch_number
    batch_number=0
    filter_str = request.args.get('filterstr', "")
    image_batch,paths = get_image_batch(batch_number,filter_str)
    return  render_template('index.html', images_with_paths=zip(image_batch,paths), batch=batch_number, filter_str=filter_str)

@app.route('/')
def index():
    global all_images
    global batch_number
    global filter_str
    if len(all_images) == 0:
        init_images()
    batch_number = int(request.args.get('batch', 0))
    image_batch,paths = get_image_batch(batch_number,filter_str)
    preload(batch_number)
    return render_template('index.html', images_with_paths=zip(image_batch,paths), batch=batch_number, filter_str=filter_str)

@app.route('/next')
def next_batch():
    global batch_number
    global filter_str
    batch_number = int(request.args.get('batch', 0)) + 1
    image_batch,paths = get_image_batch(batch_number,filter_str)
    preload(batch_number)
    return  render_template('index.html', images_with_paths=zip(image_batch,paths), batch=batch_number, filter_str=filter_str)

@app.route('/prev')
def prev_batch():
    global batch_number
    batch_number = int(request.args.get('batch', 0)) - 1
    image_batch,paths = get_image_batch(batch_number)
    return  render_template('index.html', images_with_paths=zip(image_batch,paths), batch=batch_number, filter_str=filter_str)

@app.route('/delete', methods=['POST'])
def delete_image():
    print("called delete")
    global deleted_images
    if request.method == 'POST':
        path_to_delete = request.form['path']
        deleted_images.append(path_to_delete)
        fs.remove(path_to_delete)
    return redirect(request.referrer)

if __name__ == '__main__':
        app.run(debug=True,port=5001)



