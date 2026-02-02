import asyncio
from renderer import TemplateRenderer

async def main():
    renderer = TemplateRenderer()

    html = await renderer.render(
        data={
            "summary": "Transformers use self-attention.",
            "flashcards": [
                {"question": "What is attention?", "answer": "Weighted focus on tokens"}
            ],
            "quiz": [
                {
                    "question": "Which model uses self-attention?",
                    "options": {
                        "A": "CNN",
                        "B": "RNN",
                        "C": "Transformer",
                        "D": "SVM"
                    },
                    "answer": "C"
                }
            ]
        }
    )

    with open("preview.html", "w", encoding="utf-8") as f:
        f.write(html)

    print("✅ preview.html generated")

if __name__ == "__main__":
    asyncio.run(main())
