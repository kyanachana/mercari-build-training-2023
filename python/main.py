import os
import logging
import pathlib
import json
import hashlib
import shutil
from fastapi import FastAPI, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()
logger = logging.getLogger("uvicorn")
logger.level = logging.INFO
images = pathlib.Path(__file__).parent.resolve() / "images"
origins = [ os.environ.get('FRONT_URL', 'http://localhost:3000') ]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET","POST","PUT","DELETE"],
    allow_headers=["*"],
)

def hash_image(original_image_path): #covert image to hashed image
    with open(images/original_image_path,'rb')as f:
        original_image=f.read() 
    hash=hashlib.sha256()
    hash.update(original_image)
    return hash.hexdigest()

@app.get("/")
def root():
    return {"message": "Hello, world!"}

@app.post("/items")
def add_item(name: str = Form(...), category: str = Form(...), image: UploadFile=Form(...)):
    original_image=image.filename #default.jpg
    hashed_str = str(hash_image(original_image))
    jpg_name=hashed_str+'.jpg' #ad55d25f2c10c.jpg(hashed)
    shutil.copy(images/original_image, images/jpg_name)

    new_item={"name":name,"category":category, "image_filename":jpg_name}
    logger.info(f"Receive item:{name},category:{category}, image_filename:{jpg_name}")

    try:
        with open("items.json","r")as f:
            data=json.load(f)
    except:
        data={"items":[]}

    # append new item
    with open("items.json","w")as f:
        data["items"].append(new_item)
        json.dump(data,f)
    return {"message": f"item received: {name}, category received: {category}, image_filename: {jpg_name}"}

@app.get("/items")
def get_all_item():
    try:
        with open("items.json","r")as f:
            return json.load(f)
    except:
        return {"items":[]}

@app.get("/items/{item_id}")
def get_id_item(item_id):
    try:
        with open("items.json","r")as f:
            data = json.load(f)
            return data["items"][int(item_id) - 1]
    except:
        return {"items":[]}   


@app.get("/image/{image_filename}")
async def get_image(image_filename):
    # Create image path
    image = images / image_filename

    if not image_filename.endswith(".jpg"):
        raise HTTPException(status_code=400, detail="Image path does not end with .jpg")

    if not image.exists():
        logger.debug(f"Image not found: {image}")
        image = images / "default.jpg"

    return FileResponse(image)