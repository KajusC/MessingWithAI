import inquirer
from fastapi import FastAPI
from inquirer import prompt
from scalar_fastapi import Theme, add_scalar_reference

from agent import answer
from speech import listen_for_query, transcribe_audio

app = FastAPI()
add_scalar_reference(app, route="/scalar", theme=Theme.KEPLER)


@app.get("/health")
def health_status() -> dict[str, str]:
    return {"status": "ok"}


def main() -> None:
    while True:
        question = [
            inquirer.List(
                "option",
                message="What do you want to do?",
                choices=["Push to talk", "Transcribe audio", "Ask a question"],
            )
        ]
        selected = prompt(question)
        if selected["option"] == "Push to talk":
            query = listen_for_query()
            if not query:
                print("No speech recognized.")
                continue
            print(query)
        elif selected["option"] == "Transcribe audio":
            audio_path = input("Enter the path to the audio file: ")
            query = transcribe_audio(audio_path)
            print(query)
        else:
            query = input("Enter a query: ")
        print(answer(query))


if __name__ == "__main__":
    main()
