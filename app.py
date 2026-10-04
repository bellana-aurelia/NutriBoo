from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import numpy as np
from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input, decode_predictions
from tensorflow.keras.preprocessing import image as keras_image
import shutil
import os
import uuid
import logging
import pathlib

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# App init
app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Folder setup
pathlib.Path("static").mkdir(parents=True, exist_ok=True)
pathlib.Path("templates").mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Load CNN model
model_cnn = MobileNetV2(weights="imagenet")

# Pydantic models
class CalorieNeedsRequest(BaseModel):
    age: int
    weight: float
    height: float

class PetStatusRequest(BaseModel):
    last_meal_hours: float
    healthy_food_score: float

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/predict_food")
async def predict_food(image: UploadFile = File(...)):
    file_id = str(uuid.uuid4())
    temp_path = f"temp_{file_id}.jpg"

    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    try:
        logger.info(f"Image saved to {temp_path}")
        img = keras_image.load_img(temp_path, target_size=(224, 224))
        x = keras_image.img_to_array(img)
        x = preprocess_input(np.expand_dims(x, axis=0))
        preds = model_cnn.predict(x)
        logger.info(f"Prediction done: {preds}")

        label, confidence = decode_predictions(preds, top=1)[0][0][1:]
        unhealthy = any(k in label.lower() for k in ['french fries', 'cake', 'burger', 'donut', 'soda'])

        return {
            "nama_makanan": label,
            "confidence": float(confidence),
            "status_sehat": not unhealthy
        }

    except Exception as e:
        logger.exception("Error processing image")
        raise HTTPException(status_code=500, detail="Error processing image")

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@app.post("/calorie_needs")
async def calorie_needs(data: CalorieNeedsRequest):
    try:
        bmr = 10 * data.weight + 6.25 * data.height - 5 * data.age + 5
        return {"calorie_needs": round(bmr, 2)}
    except Exception as e:
        logger.error(f"Error calculating calorie needs: {e}")
        raise HTTPException(status_code=500, detail="Gagal menghitung kalori.")

@app.post("/pet_status")
async def pet_status(data: PetStatusRequest):
    try:
        status = "Sehat" if data.healthy_food_score >= 0.5 and data.last_meal_hours <= 8 else "Perlu perhatian"
        return {
            "last_meal_hours": data.last_meal_hours,
            "healthy_food_score": data.healthy_food_score,
            "status": status
        }
    except Exception as e:
        logger.error(f"Error evaluating pet status: {e}")
        raise HTTPException(status_code=500, detail="Gagal memproses status hewan.")
