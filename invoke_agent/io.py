# io.py

class IOHandler:
    def prompt(self, message: str) -> str:
        """
        General-purpose prompt (e.g. asking for an API key).
        """
        return input(message)

    def notify(self, message: str) -> None:
        """
        General-purpose notification or logging.
        """
        print(message)

    def get_oauth_code(self) -> str:
        """
        Handle OAuth code retrieval for a given service.

        Override this in a custom IOHandler to support
        browser-based flows, Flask endpoints, etc.
        """
        return self.prompt("\n🔑 Enter the auth code: ")

# Global instance that can be overridden
io = IOHandler()

def set_io_handler(custom_handler: IOHandler):
    global io
    io = custom_handler