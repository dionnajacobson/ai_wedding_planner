import argparse

from agents.wedding_agent import WeddingAgent
from db.database import init_db
from services.wedding_service import WeddingService


def run_query_loop(
    *,
    email: str = "unknown@example.com",
    first_name: str,
    last_name: str = "Jacobson",
) -> None:
    """Run an interactive wedding planning chat using OpenAI and PostgreSQL."""
    init_db()
    wedding_service = WeddingService.default()
    agent = WeddingAgent.default()

    client = wedding_service.onboard_client(
        email=email,
        first_name=first_name,
        last_name=last_name,
    )
    session_id = wedding_service.create_session(client_id=client.id)

    print("Wedding Planner AI (OpenAI + PostgreSQL)")
    print(f"Client ID: {client.id}")
    print(f"Wedding ID: {client.wedding_id}")
    print(f"Session ID: {session_id}")
    print("Ask planning questions. Type 'quit' or 'exit' to stop.\n")

    while True:
        query = input("You: ").strip()
        if not query:
            continue
        if query.lower() in {"quit", "exit"}:
            print("Goodbye!")
            break

        message = agent.chat(query, session_id)
        print(f"\nAssistant: {message.content}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Wedding planner AI assistant")
    parser.add_argument("--first-name", default="Unknown")
    parser.add_argument("--last-name", default="Jacobson")
    parser.add_argument("--email", default="unknown@example.com")
    args = parser.parse_args()

    run_query_loop(
        first_name=args.first_name,
        last_name=args.last_name,
        email=args.email,
    )


if __name__ == "__main__":
    main()
