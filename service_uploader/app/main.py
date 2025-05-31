from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError
from sqlalchemy import create_engine, Column, Integer, Float, String, update
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from io import StringIO
import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_USER = os.getenv("POSTGRES_USER", "user")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "pass")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "coordsdb")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

try:
    Base.metadata.create_all(bind=engine)
    print("Conexión a PostgreSQL OK")
except OperationalError as e:
    print("No se pudo conectar a PostgreSQL:", e)

class Coordinate(Base):
    __tablename__ = "coordinates"
    id = Column(Integer, primary_key=True, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    postcode = Column(String, nullable=True)
    error = Column(String, nullable=True)

class PostcodeUpdate(BaseModel):
    id: int
    postcode: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def procesar_archivo(raw_csv_content: str) -> pd.DataFrame:
    df = pd.read_csv(StringIO(raw_csv_content), header=0, sep='|', names=['lat', 'lon'])

    def clean_val(x):
        if isinstance(x, str):
            x = x.replace("''", "").replace("'", "").strip().lower()
            if x in ('', 'nan', 'null'):
                return np.nan
            return x.replace(',', '.')
        return x

    for col in ['lat', 'lon']:
        df[col] = df[col].apply(clean_val)
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df = df.dropna(subset=['lat', 'lon'])
    return df[['lat', 'lon']]

@app.get("/")
def read_root():
    return {"status": "ok"}

@app.post("/update_postcode")
def update_postcode(data: PostcodeUpdate, db: Session = Depends(get_db)):
    try:
        stmt = update(Coordinate).where(Coordinate.id == data.id).values(postcode=data.postcode, error=None)
        result = db.execute(stmt)
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="ID no encontrado")
        db.commit()
        return {"message": "Postcode actualizado correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Archivo no valido")

    content = await file.read()
    decoded = content.decode("utf-8")

    try:
        df = procesar_archivo(decoded)

        if df.empty:
            raise HTTPException(status_code=400, detail="No hay coordenadas")

        df['lat'] = df['lat'].astype(float)
        df['lon'] = df['lon'].astype(float)

        valid_coords = [
            Coordinate(latitude=float(row['lat']), longitude=float(row['lon']))
            for _, row in df.iterrows()
        ]

        db.bulk_save_objects(valid_coords)
        db.commit()

        return {
            "mensaje": "Archivo procesado Ok",
            "coordenadas_insertadas": len(valid_coords)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar el archivo: {str(e)}")
