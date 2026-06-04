"""Database seed — creates sample data for development/testing."""
from datetime import datetime, timedelta, timezone
from app.extensions import db
from app.models.user import User
from app.models.course import Course
from app.models.assignment import Assignment, CATEGORIES, STATES


def seed_demo_data():
    """Seed the database with demo data for development."""

    # Check if already seeded
    if User.query.filter_by(email="demo@example.com").first():
        return False

    # Create demo user
    user = User(
        google_id="demo_google_id_12345",
        email="demo@example.com",
        name="Demo Student",
        avatar_url="https://ui-avatars.com/api/?name=Demo+Student&background=6366f1&color=fff",
        settings={
            "auto_submit": True,
            "confidence_threshold": 50,
            "reminder_frequency": "standard",
            "approval_mode": False,
            "notifications": {
                "browser": True,
                "email": False,
                "telegram": False,
            },
            "course_filters": {},
        },
    )
    db.session.add(user)
    db.session.flush()

    # Create demo courses
    courses_data = [
        {"name": "Data Structures & Algorithms", "section": "CS301", "teacher_name": "Dr. Sharma"},
        {"name": "Machine Learning", "section": "CS401", "teacher_name": "Prof. Gupta"},
        {"name": "Database Management Systems", "section": "CS302", "teacher_name": "Dr. Verma"},
        {"name": "Web Development", "section": "CS201", "teacher_name": "Prof. Singh"},
    ]

    courses = []
    for i, cd in enumerate(courses_data):
        course = Course(
            user_id=user.id,
            google_course_id=f"demo_course_{i}",
            name=cd["name"],
            section=cd["section"],
            teacher_name=cd["teacher_name"],
            synced_at=datetime.now(timezone.utc),
        )
        db.session.add(course)
        courses.append(course)

    db.session.flush()

    # Create demo assignments
    now = datetime.now(timezone.utc)
    assignments_data = [
        {
            "title": "Implement Binary Search Tree in Python",
            "description": "Write a complete BST implementation with insert, delete, search, and traversal methods. Submit as a .py file.",
            "category": "DIGITAL_ASSIGNMENT",
            "state": "IN_PROGRESS",
            "due_date": now + timedelta(days=3),
            "max_points": 100,
            "ai_confidence": 85.0,
            "course_idx": 0,
        },
        {
            "title": "Write notes on Linear Regression",
            "description": "Write handwritten notes explaining linear regression with diagrams. Upload scanned images.",
            "category": "HANDWRITTEN_ASSIGNMENT",
            "state": "HANDWRITTEN_PENDING",
            "due_date": now + timedelta(days=5),
            "max_points": 50,
            "ai_confidence": 0,
            "course_idx": 1,
        },
        {
            "title": "SQL Query Assignment - Joins and Subqueries",
            "description": "Solve the following SQL problems using JOINs and subqueries. Submit a PDF with your answers.",
            "category": "DIGITAL_ASSIGNMENT",
            "state": "WAITING_FOR_REVIEW",
            "due_date": now + timedelta(hours=12),
            "max_points": 80,
            "ai_confidence": 42.0,
            "course_idx": 2,
        },
        {
            "title": "Class Rescheduled to Monday",
            "description": "Dear students, tomorrow's class is rescheduled to Monday 10:00 AM. Sorry for the inconvenience.",
            "category": "CLASS_RESCHEDULE",
            "state": "CLASSIFIED",
            "due_date": None,
            "max_points": None,
            "ai_confidence": 92.0,
            "course_idx": 3,
        },
        {
            "title": "React Portfolio Website Project",
            "description": "Build a personal portfolio website using React. Include at least 3 pages. Deploy on GitHub Pages. Submit the GitHub repo link.",
            "category": "DIGITAL_ASSIGNMENT",
            "state": "SUBMITTED_BY_AI",
            "due_date": now - timedelta(days=1),
            "max_points": 150,
            "ai_confidence": 78.0,
            "course_idx": 3,
        },
        {
            "title": "Mid-term Exam Schedule",
            "description": "Mid-term exams will begin from next Monday. Check the attached schedule for details.",
            "category": "EXAM_NOTICE",
            "state": "CLASSIFIED",
            "due_date": None,
            "max_points": None,
            "ai_confidence": 95.0,
            "course_idx": 0,
        },
        {
            "title": "ER Diagram for Library Management System",
            "description": "Draw the ER diagram for a Library Management System. Include entities, relationships, and cardinality. Submit as PDF.",
            "category": "DIGITAL_ASSIGNMENT",
            "state": "NEW",
            "due_date": now + timedelta(days=2),
            "max_points": 60,
            "ai_confidence": 0,
            "course_idx": 2,
        },
    ]

    for ad in assignments_data:
        assignment = Assignment(
            user_id=user.id,
            course_id=courses[ad["course_idx"]].id,
            google_coursework_id=f"demo_cw_{ad['title'][:20].replace(' ', '_')}",
            title=ad["title"],
            description=ad["description"],
            category=ad["category"],
            state=ad["state"],
            due_date=ad["due_date"],
            max_points=ad["max_points"],
            ai_confidence=ad["ai_confidence"],
        )
        db.session.add(assignment)

    db.session.commit()
    return True
