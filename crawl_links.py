import sys
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://stackoverflow.com"
START_PAGE = 1
END_PAGE = 50

if len(sys.argv) == 2:
    END_PAGE = int(sys.argv[1])
elif len(sys.argv) == 3:
    START_PAGE = int(sys.argv[1])
    END_PAGE = int(sys.argv[2])


def get_questions_link(page):
    return BASE_URL + "/questions?tab=votes&pagesize=50&page=" + str(page)


question_num = 0

with open("data/question-links.txt", "w") as f:
    for i in range(START_PAGE, END_PAGE + 1):
        response = requests.get(get_questions_link(i))
        soup = BeautifulSoup(response.text, "html.parser")
        links = soup.select("h3.s-post-summary--content-title > a")
        for link in links:
            f.write(BASE_URL + link["href"] + "\n")

        question_num += len(links)
        print("Page " + str(i) + " done.")
        print("Questions in this page: " + str(len(links)))

print("Total questions: " + str(question_num))
