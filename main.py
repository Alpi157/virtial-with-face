import threading
import psycopg2
from nltk.metrics import distance
from nltk.tokenize import word_tokenize
import pyttsx3
import cv2
import os

def connect_to_database(host, user, password, db_name):
    connection = psycopg2.connect(
        host=host,
        user=user,
        password=password,
        database=db_name
    )
    return connection


def close_database_connection(connection):
    connection.close()


def handle_question(connection, question):
    with connection.cursor() as cursor:
        cursor.execute("SELECT question, answer FROM questions")
        results = cursor.fetchall()
        question = question.lower()
        question = word_tokenize(question)
        closest_question = ""
        closest_distance = float("inf")
        closest_answer = ""
        for q in results:
            q_text = q[0].lower()
            q_text = word_tokenize(q_text)
            dist = distance.edit_distance(question, q_text)
            if dist < closest_distance:
                closest_distance = dist
                closest_question = q[0]
                closest_answer = q[1]
        if closest_distance < 3:
            return closest_answer
        else:
            new_question = question + ["+++"]
            cursor.execute("INSERT INTO questions (question, answer) VALUES (%s, %s)", (' '.join(new_question), ""))
            connection.commit()
            return "Извините, у меня нет ответа на этот вопрос. Я добавил ваш вопрос в базу данных."


def configure_tts_engine():
    engine = pyttsx3.init()
    engine.setProperty('language', 'ru')
    voices = engine.getProperty('voices')
    engine.setProperty('voice', 'russian')
    return engine



def play_video(video_path, play_event, stop_event):
    cap = cv2.VideoCapture(video_path)

    fps = cap.get(cv2.CAP_PROP_FPS)

    while True:
        if play_event.wait(1):
            ret, frame = cap.read()
            if not ret:
                break
            cv2.imshow('Bot Face', frame)
            if cv2.waitKey(int(1000/fps/2)) == ord('q') or stop_event.is_set():
                break

    cap.release()
    cv2.destroyAllWindows()



def say_answer(engine, answer, play_event, stop_event):
    video_path = r'C:\Users\arman\Desktop\Project\pythonProject\bot_video.mp4'
    if os.path.exists(video_path):
        play_event.set()
        video_thread = threading.Thread(target=play_video, args=(video_path, play_event, stop_event))
        video_thread.start()


    sentences = answer.split(".")
    if len(sentences) > 3:
        answer = ".".join(sentences[:2]) + "."
    engine.say(answer)
    engine.runAndWait()


    stop_event.set()
    video_thread.join()



def main():
    connection = connect_to_database(host, user, password, db_name)

    engine = configure_tts_engine()

    play_event = threading.Event()
    stop_event = threading.Event()

    while True:
        question = input("\n Задайте ваш попрос: \n")
        answer = handle_question(connection, question)
        print(answer)

        play_event.set()
        say_answer(engine, answer, play_event, stop_event)

        play_event.clear()
        stop_event.clear()

    close_database_connection(connection)


if __name__ == "__main__":
    try:
        from config import host, user, password, db_name
        main()
    except Exception as ex:
        print("ERR with PostgreSQL: ", ex)
