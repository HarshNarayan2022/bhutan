import uuid
import numpy as np
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from backend.scripts.db.session import SessionLocal
from backend.scripts.migration_schemas.resources_models import Resource

def seed_resources():
    session = SessionLocal()

    resources = [
        Resource(
            id=str(uuid.uuid4()),
            name="Primary Crisis Hotline",
            phone="1010",
            operation_hours="24/7",
            description="Operated by the Bhutan Youth Development Fund (YDF) and the Ministry of Health, this helpline offers support for mental health issues and suicide prevention.",
            category="mental health",
            type="helpline",
            source="bhutanyouth.org",
            website="https://bhutanyouth.org"
        ),
        Resource(
            id=str(uuid.uuid4()),
            name="Emergency Line",
            phone="112",
            operation_hours="24/7",
            description="The national emergency number is for immediate assistance and is accessible via mobile and landline.",
            category="emergency",
            type="helpline",
            source="National Emergency Services", 
            website="moh.gov.bt"
        ),
        Resource(
            id=str(uuid.uuid4()),
            name="Mental Health Support Line",
            phone="1098",
            operation_hours="24/7",
            description="National helpline for children and vulnerable groups. Provides mental health support.",
            category="mental health, children",
            type="helpline",
            source="National Helpline Directory", 
        ),

        Resource(
            id=str(uuid.uuid4()),
            name="Sherig Counselling Services (MoE)",
            phone="17861294",
            operation_hours="Weekdays 9am–5pm",
            description="Counselling helpline for students and youth, staffed by trained school counselors.",
            category="youth, education, counseling",
            source="moe.gov.bt",
            website="https://sites.google.com/moe.gov.bt/sherigcounsellingservices", 
            type = "helpline"
        ),

        Resource(
            id=str(uuid.uuid4()),
            name="PEMA (Psychosocial Education and Mental Health Awareness)",
            phone="1010",
            website="https://thepema.gov.bt/",
            description="PEMA is the national nodal agency for mental health promotion and services, offering counselling, crisis intervention, and rehabilitation. They also have a helpline and offer walk-in services.",
            type="organization"
        ),
        Resource(
            id=str(uuid.uuid4()),
            name="RENEW (Respect, Educate, Nurture, and Empower Women)",
            phone="+975 2 332 159",
            website="https://renew.org.bt/",
            description="Founded by Her Majesty Gyalyum Sangay Choden Wangchuck in 2004, RENEW is a non-profit organization supporting women.",
            type="organization"
        ),
        Resource(
            id=str(uuid.uuid4()),
            name="Jigme Dorji Wangchuck National Referral Hospital",
            phone="+975 17 32 24 96",
            website="https://jdwnrh.gov.bt/",
            description="This hospital has a psychiatric ward, providing specialized mental health services.",
            type="organization"
        ),

        Resource(
            id=str(uuid.uuid4()),
            name="Bhutan Board for Certified Counselors (BBCC)",
            description="Accredits and supports professional counselors in Bhutan. Promotes ethical and culturally sensitive counseling.",
            phone=None,
            website="https://www.counselingbhutan.com",
            address="Thimphu",
            type="organization"
        ),

        Resource(
        id=str(uuid.uuid4()),
        name="Institute of Traditional Medicine Services",
        description="Provides traditional Bhutanese medical treatments, including mental and spiritual healing.",
        phone=None,
        website=None,
        address="Langjophakha, Thimphu",
        type="organization"
        )
    ]

    try:
        for resource in resources:
            session.add(resource)
        session.commit()
        print(f"✅ Inserted {len(resources)} resources into DB.")
    except IntegrityError as e:
        session.rollback()
        print(f"⚠️ Duplicate detected, skipping existing entries: {str(e)}")
    except SQLAlchemyError as e:
        session.rollback()
        print(f"❌ Failed to seed: {str(e)}")
    finally:
        session.close()


def main():
    seed_resources()


if __name__ == "__main__":
    main()
