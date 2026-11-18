from flask import Flask, render_template


class ErrorController:
    """Error pages, so a failure never shows a stack trace to the user."""

    def register(self, app: Flask) -> None:
        app.register_error_handler(404, self.not_found)
        app.register_error_handler(500, self.server_error)

    def not_found(self, error):
        return render_template("errors/404.html"), 404

    def server_error(self, error):
        return render_template("errors/500.html"), 500
