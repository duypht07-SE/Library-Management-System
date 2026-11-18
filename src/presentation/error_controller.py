from flask import Flask, render_template


class ErrorController:
    """Error pages, so a failure never shows a stack trace to the user."""

    def register(self, app: Flask) -> None:
        app.register_error_handler(400, self.bad_request)
        app.register_error_handler(403, self.forbidden)
        app.register_error_handler(404, self.not_found)
        app.register_error_handler(413, self.too_large)
        app.register_error_handler(500, self.server_error)

    def bad_request(self, error):
        return render_template("errors/400.html"), 400

    def forbidden(self, error):
        return render_template("errors/403.html"), 403

    def not_found(self, error):
        return render_template("errors/404.html"), 404

    def too_large(self, error):
        return render_template("errors/413.html"), 413

    def server_error(self, error):
        return render_template("errors/500.html"), 500
