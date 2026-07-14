
from app.database import SessionLocal, engine, Base
from app import models

Base.metadata.create_all(bind=engine)
db = SessionLocal()

demo_hcps = [
    {"name": "Dr. Anjali Mehta", "specialty": "Cardiology", "hospital": "Fortis Bengaluru", "tier": "High Value"},
    {"name": "Dr. Rohan Kapoor", "specialty": "Endocrinology", "hospital": "Apollo Chennai", "tier": "Growth"},
    {"name": "Dr. Sara Iyer", "specialty": "Oncology", "hospital": "Tata Memorial Mumbai", "tier": "High Value"},
]

for h in demo_hcps:
    exists = db.query(models.HCP).filter(models.HCP.name == h["name"]).first()
    if not exists:
        db.add(models.HCP(**h))

db.commit()
print("Seeded demo HCPs.")
