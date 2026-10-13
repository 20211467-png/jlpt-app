from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import psycopg2
from psycopg2.extras import RealDictCursor
import random
import re
import os

app = FastAPI()


app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/health")
def health_check():
    return{"status":"ok"}


def is_hiragana_only(text:str)->bool:
    if not text:
        return False
    return bool(re.fullmatch(r":[\u3040-\u309F-\s]+",text.strip()))

@app.get("/test",response_class = HTMLResponse)
def test_page(request: Request):
    return templates.TemplateResponse("test.html",{"request":request})

@app.get("/api/test")
def get_test_questions():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory = RealDictCursor)

    cur.execute("""
    SELECT kanji,yomi,COALESCE(meaning,'-') AS meaning
    FROM N1Word
    WHERE kanji IS NOT NULL
        AND kanji != ''
        AND meaning IS NOT NULL
        AND meaning !=''
        AND meaning !='-'
    """)
    all_words = cur.fetchall()


#랜덤 20문제 가져오기
    cur.execute("""
    SELECT kanji,yomi,COALESCE(meaning,'-') AS meaning
    FROM N1Word
    WHERE kanji IS NOt NULL
        AND kanji != ''
        AND meaning IS NOT NULL
        AND meaning !=''
        AND meaning !='-'
    ORDER BY RANDOM()
    LIMIT 50
    """)
    target_words =cur.fetchall()

    cur.close()
    conn.close()

    questions= []

    for target in target_words:
        kanji = target["kanji"].strip()
        yomi = target["yomi"].strip() if target['yomi']else""
        meaning = target["meaning"].strip()

        if is_hiragana_only(kanji) or not yomi:
            answer_type = "meaning"
            answer_label = "한글 뜻"
            correct_answer = meaning
        else:
            answer_type = random.choice(["yomi","meaning"])

            if answer_type == "yomi":
                answer_label = "요미가타"
                correct_answer = yomi
            else:
                answer_label = "한글 뜻"
                correct_answer = meaning

        wrong_candidates = []

        for item in all_words:
            if(
                item["kanji"] == target["kanji"]
                and item["yomi"] == target["yomi"]
                and item["meaning"] == target["meaning"]
            ):
                continue
            if answer_type == "yomi":
                value = item["yomi"].strip() if item["yomi"] else ""
            else:
                value = item["meaning"].strip() if item["meaning"] else ""

            if value and value != correct_answer and value not in wrong_candidates:
                wrong_candidates.append(value)
        
        if len(wrong_candidates)<3:
            continue
        options = random.sample(wrong_candidates,3)
        options.append(correct_answer)
        random.shuffle(options)

        questions.append({
            "kanji" : kanji,
            "question" :kanji,
            "answer_type":answer_type,
            "answer_label":answer_label,
            "answer" :correct_answer,
            "options":options
            })
        if len(questions)>=20:
            break

    return{
            "questions":questions
    }




def get_db_connection():
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        database="postgres",
        user="postgres",
        password=os.environ["DB_PASSWORD"],
        sslmode="require"
    )


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/words", response_class=HTMLResponse)
def words_page(request: Request):
    return templates.TemplateResponse("words.html", {"request": request})


@app.get("/api/words")
def get_words(page: int = 1, limit: int = 10):
    if page < 1:
        page = 1

    offset = (page - 1) * limit

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # 전체 개수
    cur.execute("""
        SELECT COUNT(*) AS total_count
        FROM N1Word
    """)
    total_count = cur.fetchone()["total_count"]
    total_pages = (total_count + limit - 1) // limit if total_count > 0 else 1

    # 🔥 NULL 처리 포함
    cur.execute("""
        SELECT 
            kanji,
            yomi,
            COALESCE(meaning, '-') AS meaning
        FROM N1Word
        LIMIT %s OFFSET %s
    """, (limit, offset))

    rows = cur.fetchall()

    words = []
    for row in rows:
        words.append({
            "kanji": row["kanji"],
            "reading": row["yomi"],
            "meaning": row["meaning"],
        })

    cur.close()
    conn.close()

    return {
        "page": page,
        "limit": limit,
        "total_count": total_count,
        "total_pages": total_pages,
        "items": words
        }
