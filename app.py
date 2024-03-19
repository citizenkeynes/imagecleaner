import os
import base64
from flask import Flask, render_template, request,redirect
import concurrent
import concurrent.futures
from PIL import Image
from io import BytesIO
import threading

app = Flask(__name__)

IMAGE_DIR = '/Users/csommeregger/Library/CloudStorage/GoogleDrive-christian.sommeregger@gmail.com/My Drive/lola/scrapes/'
BATCH_SIZE = 100
global all_images
global deleted_images
global cached_images
deleted_images=[]
all_images=[]
cached_images={}

def encode_image(image_path):
    global cached_images
    if cached_images.get(image_path) is not None:
        return cached_images[image_path]
    with open(os.path.join(IMAGE_DIR, image_path), "rb") as f:
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
    global all_images
    for root, _, files in os.walk(IMAGE_DIR):
        print(root)
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                all_images.append(os.path.relpath(os.path.join(root, file), IMAGE_DIR))
    print(len(all_images))

def get_image_batch(batch_number,function="regular call"):
    global all_images
    start_idx = batch_number * BATCH_SIZE
    end_idx = start_idx + BATCH_SIZE

    if end_idx>len(all_images):
        end_idx = len(all_images)
    rel_images = [img for img in all_images[start_idx:end_idx] if img not in deleted_images]
    encoded_batch = encode_batch(rel_images)
    print(f"return {len(encoded_batch)} images and {len(rel_images)} paths images: {function}")
    return encoded_batch,rel_images

@app.route('/')
def index():
    init_images()
    batch_number = int(request.args.get('batch', 0))
    image_batch,paths = get_image_batch(batch_number)
    return render_template('index.html', images_with_paths=zip(image_batch,paths), batch=batch_number)

@app.route('/next')
def next_batch():
    batch_number = int(request.args.get('batch', 0)) + 1
    image_batch,paths = get_image_batch(batch_number)
    thread  = threading.Thread(target=get_image_batch, args=(batch_number + 1,"cache"))
    thread.start()
    return  render_template('index.html', images_with_paths=zip(image_batch,paths), batch=batch_number)

@app.route('/prev')
def prev_batch():
    batch_number = int(request.args.get('batch', 0)) - 1
    image_batch,paths = get_image_batch(batch_number)
    return  render_template('index.html', images_with_paths=zip(image_batch,paths), batch=batch_number)

@app.route('/delete', methods=['POST'])
def delete_image():
    print("called delete")
    global deleted_images
    if request.method == 'POST':
        path_to_delete = request.form['path']
        deleted_images.append(path_to_delete)
        os.remove(os.path.join(IMAGE_DIR, path_to_delete))
    return redirect(request.referrer)

@app.route('/clean', methods=['GET'])
def clean():
    global deleted_images
    for image in deleted_images:
        os.remove(os.path.join(IMAGE_DIR, image))
        print(f"deleted {image}")
    return redirect(request.referrer)

if __name__ == '__main__':
        app.run(debug=True,port=5001)



