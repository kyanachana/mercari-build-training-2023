import os
import logging
import pathlib
import json
import hashlib
import re
import shutil
import sqlite3
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

def table_isexist(db_cursor):
    db_cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE TYPE = 'table' AND name = 'items'")
    if db_cursor.fetchone()[0] == 0:
        return False
    return True  

def open_database():
    db_connect = sqlite3.connect("../db/mercari.sqlite3", check_same_thread=False)
    db_cursor = db_connect.cursor()
    if table_isexist(db_cursor) == False: # if there's no table, create new table
        db_connect.execute("CREATE TABLE items(id integer primary key,name text,category_id integer,image_filename text)")
        db_connect.execute("CREATE TABLE category(id integer primary key,name text)")
    return (db_connect,db_cursor)

def hash_image(original_image_path): #covert image to hashed image
    with open(images/original_image_path,'rb')as f:
        original_image=f.read() 
    hash=hashlib.sha256()
    hash.update(original_image)
    return hash.hexdigest()

def align_data_format(data_items):
    items_dict = {"items": []}
    for item in data_items:
        new_item={"name": item[0],"category": item[1],"image": item[2]}    
        items_dict["items"].append(new_item)
    return items_dict

@app.get("/")
def root():
    return {"message": "Hello, world!"}

@app.post("/items")
def add_item(name: str = Form(...), category: str = Form(...), image: UploadFile=Form(...)):
    (db_connect, db_cursor) = open_database()

    # image -> hashed image
    original_image=image.filename #default.jpg
    hashed_str = str(hash_image(original_image))
    jpg_name=hashed_str+'.jpg' #ad55d25f2c10c.jpg(hashed)
    shutil.copy(images/original_image, images/jpg_name)
    
    # add new item to database
    db_cursor.execute("SELECT id FROM category WHERE name = ?",(category,))
    category_id_check = db_cursor.fetchall()
    if category_id_check == []: # new category
        db_cursor.execute("INSERT INTO category(name) VALUES(?)",(category,))
        db_cursor.execute("SELECT id FROM category WHERE name = ?",(category,))
        category_id = db_cursor.fetchall()[0][0]
        db_cursor.execute("INSERT INTO items(name, category_id,image_filename) VALUES(?,?,?)",(name,category_id,jpg_name,))
    else: # already exist category
        category_id = category_id_check[0][0]
        db_cursor.execute("INSERT INTO items(name, category_id,image_filename) VALUES(?,?,?)",(name,category_id,jpg_name,))

    db_connect.commit()
    db_connect.close()
    logger.info(f"Receive item:{name},category:{category}, image_filename:{jpg_name}")
    return {"message": f"item received: {name}, category received: {category}, image_filename: {jpg_name}"}

@app.get("/items")
def get_all_item():
    (db_connect, db_cursor) = open_database()

    sql = "SELECT items.name, category.name, items.image_filename FROM items INNER JOIN category ON items.category_id = category.id"
    db_cursor.execute(sql)    
    data_items = db_cursor.fetchall()
    db_connect.close()
    return align_data_format(data_items)

@app.get("/search")
def search_name(keyword:str):
    (db_connect, db_cursor) = open_database()

    # select by items.name
    sql = "SELECT items.name, category.name, items.image_filename FROM items INNER JOIN category ON items.category_id = category.id WHERE items.name = ?"
    db_cursor.execute(sql,(keyword,))
    data_items = db_cursor.fetchall()
    db_connect.close()
    return align_data_format(data_items)


@app.get("/items/{item_id}")
def get_id_item(item_id):
    (db_connect, db_cursor) = open_database()

    # select by items.id
    sql = "SELECT items.name, category.name, items.image_filename FROM items INNER JOIN category ON items.id = ?"
    db_cursor.execute(sql,item_id)    
    data_items = db_cursor.fetchall()

    db_connect.close()
    return align_data_format(data_items)

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