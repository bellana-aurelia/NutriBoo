from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import numpy as np
from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input, decode_predictions
from tensorflow.keras.preprocessing import image
import shutil
import os
import uuid
import logging

# Inisialisasi logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Food Classification & Health API",
    description="API untuk klasifikasi makanan dan perhitungan kebutuhan kalori serta status hewan peliharaan.",
    version="1.0.0"
)

# ===== CORS setup =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ganti "*" ke asal domain frontend yang sah jika sudah production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== Tambahan: Static dan Templates =====
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ===== Load model sekali saat startup =====
logger.info("Loading MobileNetV2 model...")
model_cnn = MobileNetV2(weights='imagenet')
logger.info("Model loaded.")

# ===== Data Models =====
class CalorieNeedsRequest(BaseModel):
    age: int
    weight: float
    height: float

class PetStatusRequest(BaseModel):
    last_meal_hours: float
    healthy_food_score: float

# ===== Utility Functions =====
def classify_food(image_path: str):
    img = image.load_img(image_path, target_size=(224, 224))
    x = image.img_to_array(img)
    x = preprocess_input(np.expand_dims(x, axis=0))
    preds = model_cnn.predict(x)
    decoded = decode_predictions(preds, top=1)[0][0]  # (class_id, class_name, score)
    return decoded[1], float(decoded[2])  # (label, confidence)

def is_unhealthy(food_label: str):
    unhealthy_keywords = ['french fries', 'cake', 'burger', 'donut', 'soda']
    return any(keyword in food_label.lower() for keyword in unhealthy_keywords)

# ===== Routes =====

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
        label, confidence = classify_food(temp_path)
        unhealthy = is_unhealthy(label)
        return {
            "nama_makanan": label,
            "confidence": confidence,
            "status_sehat": not unhealthy
        }
    except Exception as e:
        logger.error(f"Error during food classification: {e}")
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
        logger.error(f"Error during calorie needs calculation: {e}")
        raise HTTPException(status_code=500, detail="Error calculating calorie needs")

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
        logger.error(f"Error during pet status check: {e}")
        raise HTTPException(status_code=500, detail="Error processing pet status")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error"},
    )
