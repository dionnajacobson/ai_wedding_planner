import argparse
from agents.client.openai_client import OpenAIClient
from agents.prompts.prompts import WeddingPromptJinja


def run_query_loop(
    *,
    couple_names: str = "Unknown",
    wedding_date: str = "Unknown",
    budget: str = "Unknown",
    model: str = "gpt-4.1-mini",
) -> None:
    """Run an interactive wedding planning chat using OpenAI."""
    client = OpenAIClient(model=model)
    prompt = WeddingPromptJinja(
        couple_names=couple_names,
        wedding_date=wedding_date,
        budget=budget,
    )
    base_prompt = prompt.render()

    print("Wedding Planner AI (OpenAI)")
    print("Ask planning questions. Type 'quit' or 'exit' to stop.\n")

    while True:
        query = input("You: ").strip()
        if not query:
            continue
        if query.lower() in {"quit", "exit"}:
            print("Goodbye!")
            break

        llm_input = base_prompt.model_copy(update={"user": query})
        response = client.invoke(input=llm_input)
        print(f"\nAssistant: {response.text}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Wedding planner AI assistant")
    parser.add_argument("--couple-names", default="Unknown")
    parser.add_argument("--wedding-date", default="Unknown")
    parser.add_argument("--budget", default="Unknown")
    parser.add_argument("--model", default="gpt-4.1-mini")
    args = parser.parse_args()

    run_query_loop(
        couple_names=args.couple_names,
        wedding_date=args.wedding_date,
        budget=args.budget,
        model=args.model,
    )


if __name__ == "__main__":
    main()
