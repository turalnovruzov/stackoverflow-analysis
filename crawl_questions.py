import requests
import sys
from datetime import datetime
from bs4 import BeautifulSoup
import sqlite3

BASE_URL = "https://stackoverflow.com"
QUESTIONS_FILE_NAME = "data/question-links.txt"
DB_FILE_NAME = "data/database.db"
START_LINK_NUM = 1
END_LINK_NUM = None

if len(sys.argv) == 2:
    START_LINK_NUM = int(sys.argv[1])
elif len(sys.argv) == 3:
    START_LINK_NUM = int(sys.argv[1])
    END_LINK_NUM = int(sys.argv[2])
elif len(sys.argv) == 4:
    START_LINK_NUM = int(sys.argv[1])
    END_LINK_NUM = int(sys.argv[2])
    DB_FILE_NAME = sys.argv[3]
elif len(sys.argv) == 5:
    START_LINK_NUM = int(sys.argv[1])
    END_LINK_NUM = int(sys.argv[2])
    DB_FILE_NAME = sys.argv[3]
    QUESTIONS_FILE_NAME = sys.argv[4]

conn = sqlite3.connect('data/database.db')
cursor = conn.cursor()

all_tags_ids = {}

question_num = 0
answer_num = 0
tag_num = 0


def get_question_links():
    """
    Get all question links from the file QUESTIONS_FILE_NAME

    Returns:
        List<string>: Question links
    """
    question_links = []
    with open(QUESTIONS_FILE_NAME, "r") as f:
        for line in f:
            question_links.append(line.strip())
    return question_links


def get_question_data(link):
    """
    Get all question data from the link and save to the database

    Args:
        link (string): link to the question website
    """
    global question_num, answer_num, tag_num
    # Get question data
    page = requests.get(link)
    soup = BeautifulSoup(page.text, 'html.parser')

    # Get the question data
    question = {}

    question["title"] = soup.select("div#question-header > h1 > a.question-hyperlink")[0].text
    question["body_with_tags"] = soup.select("div#question div.js-post-body")[0].prettify()
    question["body_without_tags"] = soup.select("div#question div.js-post-body")[0].get_text()
    question["votes"] = int(soup.select("div#question div.js-vote-count")[0].text)
    question["url"] = BASE_URL + soup.select("div#question a.js-share-link")[0].get("href")
    viewed_text = soup.select("div.inner-content > div:nth-child(2) > div:nth-child(3)")[0].get("title")
    question["views"] = int(viewed_text.split(" ")[1].replace(",", ""))
    created_datetime_str = soup.select("div.inner-content > div:nth-child(2) > div:nth-child(1)")[0].get("title")
    question["created_date"] = datetime.strptime(created_datetime_str, "%Y-%m-%d %H:%M:%SZ")
    modified_datetime_str = soup.select("div.inner-content > div:nth-child(2) > div:nth-child(2) > a")[0].get("title")
    question["modified_date"] = datetime.strptime(modified_datetime_str, "%Y-%m-%d %H:%M:%SZ")

    # Get the answers data
    answers = []
    answers_html = soup.select("div#answers > div.answer")
    for answer_html in answers_html:
        answer = {}
        answer["body_with_tags"] = answer_html.select("div.js-post-body")[0].prettify()
        answer["body_without_tags"] = answer_html.select("div.js-post-body")[0].get_text()
        answer["votes"] = int(answer_html.select("div.js-vote-count")[0].text)
        answer["url"] = BASE_URL + answer_html.select("a.js-share-link")[0].get("href")
        answer["accepted"] = "accepted-answer" in answer_html["class"]
        created_datetime_str = answer_html.select("time")[0].get("datetime")
        answer["created_date"] = datetime.strptime(created_datetime_str, "%Y-%m-%dT%H:%M:%S")
        answers.append(answer)

    # Get the tags data
    tags = []
    tags_html = soup.select("div#question li.js-post-tag-list-item > a")
    for tag_html in tags_html:
        tag = {}
        tag["name"] = tag_html.text
        tag["url"] = BASE_URL + tag_html.get("href")
        tags.append(tag)

    # Save the question data to the database
    try:
        cursor.execute("""
                INSERT INTO Question 
                (title, body_with_tags, body_without_tags, votes, url, views, created_date, modified_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (question["title"], question["body_with_tags"], question["body_without_tags"], question["votes"], question["url"], question["views"], question["created_date"], question["modified_date"]))

        question_id = cursor.lastrowid
        question_num += 1
    except sqlite3.IntegrityError:
        return

    # Save the answers data to the database
    for answer in answers:
        cursor.execute("""
            INSERT INTO Answer 
            (body_with_tags, body_without_tags, votes, url, accepted, created_date, question_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (answer["body_with_tags"], answer["body_without_tags"], answer["votes"], answer["url"], answer["accepted"], answer["created_date"], question_id))
    answer_num += len(answers)

    # Save the tags data to the database
    for tag in tags:
        if tag["name"] in all_tags_ids:
            tag_id = all_tags_ids[tag["name"]]
        else:
            cursor.execute("""
                INSERT INTO Tag 
                (name, url)
                VALUES (?, ?)
            """, (tag["name"], tag["url"]))
            tag_id = cursor.lastrowid
            all_tags_ids[tag["name"]] = tag_id
            tag_num += 1

        cursor.execute("""
            INSERT INTO Question_Tag
            (question_id, tag_id)
            VALUES (?, ?)
        """, (question_id, tag_id))


def read_all_tags():
    """
    Read all tags from the database
    """
    cursor.execute("SELECT id, name FROM Tag")
    for row in cursor.fetchall():
        all_tags_ids[row[1]] = row[0]


def get_all_question_data():
    """
    Get all question data from the file QUESTIONS_FILE_NAME and save to the database
    """
    global END_LINK_NUM, question_num, answer_num, tag_num
    question_links = get_question_links()
    END_LINK_NUM = len(question_links) + 1 if END_LINK_NUM is None else END_LINK_NUM
    for i in range(START_LINK_NUM - 1, END_LINK_NUM - 1):
        if i % 10 == 0:
            print(f"At Question {i}")
            print(f"Added -- Question: {question_num}, Answer: {answer_num}, Tag: {tag_num}")
            conn.commit()
        get_question_data(question_links[i])


read_all_tags()
get_all_question_data()

# Print total number of questions, answers, tags in the database by reading from database
cursor.execute("SELECT COUNT(*) FROM Question")
question_num_db = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM Answer")
answer_num_db = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM Tag")
tag_num_db = cursor.fetchone()[0]
print(f"Total -- Question: {question_num_db}, Answer: {answer_num_db}, Tag: {tag_num_db}")


conn.commit()
conn.close()
