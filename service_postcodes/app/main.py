from fastapi import FastAPI, HTTPException
import requests
import psycopg2
import os

app = FastAPI()

DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "coordsdb")
DB_USER = os.getenv("DB_USER", "user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "pass")

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

@app.get("/update-postcodes")
def update_postcodes():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, latitude, longitude FROM coordinates WHERE postcode IS NULL AND error IS NULL"
                )
                rows = cursor.fetchall()

                updated = []
                errors = []

                for coord_id, lat, lon in rows:
                    try:
                        res = requests.get(
                            "https://api.postcodes.io/postcodes",
                            params={"lon": lon, "lat": lat},
                            timeout=5
                        )
                        if res.status_code == 200:
                            data = res.json()
                            postcode = None
                            if data.get("status") == 200 and isinstance(data.get("result"), list) and len(data["result"]) > 0:
                                postcode = data["result"].get("postcode")

                            if postcode:
                                cursor.execute(
                                    "UPDATE coordinates SET postcode = %s, error = NULL WHERE id = %s",
                                    (postcode, coord_id)
                                )
                                updated.append({"id": coord_id, "postcode": postcode})
                            else:
                                cursor.execute(
                                    "UPDATE coordinates SET error = %s WHERE id = %s",
                                    ("No postcode found", coord_id)
                                )
                                errors.append({"id": coord_id, "error": "No found"})
                        else:
                            cursor.execute(
                                "UPDATE coordinates SET error = %s WHERE id = %s",
                                (f"API error {res.status_code}", coord_id)
                            )
                            errors.append({"id": coord_id, "error": f"API error {res.status_code}"})
                    except Exception as e:
                        cursor.execute(
                            "UPDATE coordinates SET error = %s WHERE id = %s",
                            (str(e), coord_id)
                        )
                        errors.append({"id": coord_id, "error": str(e)})

                conn.commit()
                return {"updated": updated, "errors": errors}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/")
def health_check():
    return {"status": "service running"}
