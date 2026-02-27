from app import create_app

application = create_app()


@application.get("/health")
def health():
    return "ok", 200

if __name__ == "__main__":
    application.run()