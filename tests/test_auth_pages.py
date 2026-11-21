"""System tests for 0.2.0: sign in, roles, cards, staff, and rules."""
import io
import re

PASSWORD = "Library@123"
TOKEN_PATTERN = re.compile(r'name="csrf_token"\s+value="([^"]+)"')


def csrf_token(client, url: str) -> str:
    response = client.get(url)
    match = TOKEN_PATTERN.search(response.get_data(as_text=True))
    assert match, f"no CSRF token on {url}"
    return match.group(1)


def signin(client, email: str, password: str = PASSWORD):
    token = csrf_token(client, "/signin")
    return client.post("/signin", data={
        "csrf_token": token, "email": email, "password": password,
    })


def post_form(client, token_url: str, action: str, data: dict,
              follow_redirects: bool = True):
    payload = {"csrf_token": csrf_token(client, token_url)}
    payload.update(data)
    return client.post(action, data=payload,
                       follow_redirects=follow_redirects)


def register_form(client, **overrides):
    fields = {
        "full_name": "Nguyen Van Moi", "student_id": "22529999",
        "email": "moi@library.test", "phone": "0912345678",
        "password": "Secret123", "confirmation": "Secret123",
    }
    fields.update(overrides)
    return post_form(client, "/register", "/register", fields)


# --- Pages ----------------------------------------------------------------
def test_signin_page_has_form_and_register_link(client):
    page = client.get("/signin").get_data(as_text=True)
    assert "Sign In" in page
    assert "Create account" in page
    assert "Five wrong passwords" in page


def test_register_page_has_all_required_fields(client):
    page = client.get("/register").get_data(as_text=True)
    for field in ["full_name", "student_id", "email", "phone",
                  "password", "confirmation"]:
        assert f'name="{field}"' in page


# --- Registration ---------------------------------------------------------
def test_guest_registers_a_pending_reader(client, library_app):
    response = register_form(client)
    assert response.status_code == 200
    assert "Account created" in response.get_data(as_text=True)
    reader = library_app.users.find_by_email("moi@library.test")
    assert reader.status.value == "PENDING"
    assert reader.student_id == "22529999"
    assert reader.card_code is None


def test_duplicate_email_is_reported(client):
    response = register_form(client, email="reader@library.test")
    assert response.status_code == 400
    assert "already registered" in response.get_data(as_text=True)


def test_weak_password_is_reported(client):
    response = register_form(client, password="short", confirmation="short")
    assert response.status_code == 400
    assert "at least 8 characters" in response.get_data(as_text=True)


def test_mismatched_passwords_are_reported(client):
    response = register_form(client, confirmation="Different123")
    assert response.status_code == 400
    assert "do not match" in response.get_data(as_text=True)


# --- Sign in and sign out -------------------------------------------------
def test_reader_signs_in_and_sees_the_account_menu(client):
    response = signin(client, "reader@library.test")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")
    page = client.get("/").get_data(as_text=True)
    assert "Sign Out" in page
    assert "Nguyen Van An" in page
    assert "My Profile" in page


def test_wrong_password_shows_an_error(client):
    response = signin(client, "reader@library.test", "wrong")
    assert response.status_code == 401
    assert "Invalid email or password" in response.get_data(as_text=True)


def test_sql_injection_email_is_safe(client):
    response = signin(client, "' OR 1=1 --", "anything")
    assert response.status_code == 401
    assert "Invalid email or password" in response.get_data(as_text=True)


def test_five_wrong_passwords_lock_the_account(client, library_app):
    for _ in range(5):
        response = signin(client, "reader3@library.test", "wrong")
    assert response.status_code == 401
    assert "locked for 15 minutes" in response.get_data(as_text=True)
    user = library_app.users.find_by_email("reader3@library.test")
    assert user.locked_until is not None
    response = signin(client, "reader3@library.test")
    assert "Try again after" in response.get_data(as_text=True)


def test_pending_card_cannot_sign_in(client):
    response = signin(client, "pending@library.test")
    assert response.status_code == 401
    assert "waiting for approval" in response.get_data(as_text=True)


def test_locked_card_cannot_sign_in(client):
    response = signin(client, "locked@library.test")
    assert response.status_code == 401
    assert "account is locked" in response.get_data(as_text=True)


def test_sign_in_does_not_redirect_to_another_site(client):
    token = csrf_token(client, "/signin")
    response = client.post("/signin?next=//evil.test", data={
        "csrf_token": token, "email": "reader@library.test",
        "password": PASSWORD,
    })
    assert response.status_code == 302
    assert response.headers["Location"] == "/"


def test_sign_out_ends_the_session(client):
    signin(client, "reader@library.test")
    response = post_form(client, "/", "/signout", {})
    page = response.get_data(as_text=True)
    assert "You have signed out" in page
    assert "Sign In" in page
    assert client.get("/profile").status_code == 302


# --- Role-based access ----------------------------------------------------
def test_guest_is_sent_to_sign_in_for_profile(client):
    response = client.get("/profile")
    assert response.status_code == 302
    assert "/signin" in response.headers["Location"]


def test_reader_cannot_open_librarian_or_admin_pages(client):
    signin(client, "reader@library.test")
    assert client.get("/librarian/readers").status_code == 403
    assert client.get("/admin/librarians").status_code == 403
    assert client.get("/admin/rules").status_code == 403


def test_librarian_cannot_open_reader_or_admin_pages(client):
    signin(client, "librarian@library.test")
    assert client.get("/profile").status_code == 403
    assert client.get("/admin/rules").status_code == 403


def test_administrator_cannot_open_librarian_pages(client):
    signin(client, "admin@library.test")
    assert client.get("/librarian/readers").status_code == 403
    assert client.get("/profile").status_code == 403


def test_a_locked_session_ends_on_the_next_request(client, library_app):
    signin(client, "reader@library.test")
    with library_app.database.transaction() as conn:
        conn.execute("UPDATE users SET status = 'LOCKED' WHERE user_id = 3")
    response = client.get("/profile")
    assert response.status_code == 302
    assert "/signin" in response.headers["Location"]


# --- Profile --------------------------------------------------------------
def test_reader_updates_profile(client, library_app):
    signin(client, "reader@library.test")
    response = post_form(client, "/profile", "/profile", {
        "full_name": "Nguyen Van Binh", "student_id": "22520001",
        "email": "binh@library.test", "phone": "0911111111",
    })
    page = response.get_data(as_text=True)
    assert "profile has been updated" in page
    assert "Nguyen Van Binh" in page
    assert library_app.users.find_by_email("binh@library.test") is not None


def test_profile_rejects_another_account_email(client):
    signin(client, "reader@library.test")
    response = post_form(client, "/profile", "/profile", {
        "full_name": "Nguyen Van An", "student_id": "22520001",
        "email": "reader2@library.test", "phone": "0900000003",
    })
    assert response.status_code == 400
    assert "already registered" in response.get_data(as_text=True)


def test_reader_changes_password_and_signs_in_with_it(client):
    signin(client, "reader@library.test")
    response = post_form(client, "/profile", "/profile/password", {
        "current_password": PASSWORD, "new_password": "Changed456",
        "confirmation": "Changed456",
    })
    assert "password has been changed" in response.get_data(as_text=True)
    post_form(client, "/", "/signout", {})
    response = signin(client, "reader@library.test", "Changed456")
    assert response.status_code == 302


def test_change_password_rejects_a_wrong_current_password(client):
    signin(client, "reader@library.test")
    response = post_form(client, "/profile", "/profile/password", {
        "current_password": "wrong", "new_password": "Changed456",
        "confirmation": "Changed456",
    })
    assert "current password is incorrect" in response.get_data(as_text=True)


def test_reader_uploads_an_avatar(client, library_app):
    signin(client, "reader@library.test")
    token = csrf_token(client, "/profile")
    image = b"\x89PNG\r\n\x1a\n" + b"0" * 40
    response = client.post(
        "/profile/avatar",
        data={"csrf_token": token, "avatar": (io.BytesIO(image), "me.png")},
        content_type="multipart/form-data", follow_redirects=True)
    assert "avatar has been updated" in response.get_data(as_text=True)
    stored = library_app.users.find_by_id(3).avatar_path
    assert stored and stored.endswith(".png")
    avatar = client.get(f"/avatar/{stored}")
    assert avatar.status_code == 200
    assert avatar.data == image


def test_avatar_must_be_an_image(client):
    signin(client, "reader@library.test")
    token = csrf_token(client, "/profile")
    response = client.post(
        "/profile/avatar",
        data={"csrf_token": token,
              "avatar": (io.BytesIO(b"not an image"), "me.png")},
        content_type="multipart/form-data", follow_redirects=True)
    assert "must be a PNG" in response.get_data(as_text=True)


def test_avatar_over_2_mb_is_rejected(client):
    signin(client, "reader@library.test")
    token = csrf_token(client, "/profile")
    big = b"\x89PNG\r\n\x1a\n" + b"0" * (2 * 1024 * 1024 + 20)
    response = client.post(
        "/profile/avatar",
        data={"csrf_token": token, "avatar": (io.BytesIO(big), "big.png")},
        content_type="multipart/form-data", follow_redirects=True)
    assert "must be 2 MB or smaller" in response.get_data(as_text=True)


def test_request_over_100_mb_shows_file_too_large(client):
    signin(client, "reader@library.test")
    token = csrf_token(client, "/profile")
    big = b"0" * (100 * 1024 * 1024 + 1)
    response = client.post(
        "/profile/avatar",
        data={"csrf_token": token, "avatar": (io.BytesIO(big), "big.png")},
        content_type="multipart/form-data")
    assert response.status_code == 413
    assert "File Too Large" in response.get_data(as_text=True)


# --- Librarian screens ----------------------------------------------------
def test_librarian_sees_reader_cards(client):
    signin(client, "librarian@library.test")
    page = client.get("/librarian/readers").get_data(as_text=True)
    assert "Reader Cards" in page
    assert "Pham Minh Chau" in page
    assert "22520003" in page
    assert "Approve" in page


def test_librarian_approves_a_new_card(client, library_app):
    register_form(client, email="approve@library.test",
                  phone="0912345670", student_id="22529998")
    new_id = library_app.users.find_by_email("approve@library.test").user_id

    signin(client, "librarian@library.test")
    response = post_form(client, "/librarian/readers",
                         f"/librarian/readers/{new_id}/approve", {})
    assert "approved" in response.get_data(as_text=True)
    approved = library_app.users.find_by_id(new_id)
    assert approved.status.value == "ACTIVE"
    assert approved.card_code == f"RD-{new_id:04d}"

    other = library_app.flask.test_client()
    assert signin(other, "approve@library.test",
                  "Secret123").status_code == 302


def test_librarian_rejects_a_pending_card(client, library_app):
    signin(client, "librarian@library.test")
    response = post_form(client, "/librarian/readers",
                         "/librarian/readers/5/reject", {})
    assert "rejected" in response.get_data(as_text=True)
    assert library_app.users.find_by_id(5).status.value == "REJECTED"


def test_librarian_locks_and_unlocks_a_card(client, library_app):
    signin(client, "librarian@library.test")
    post_form(client, "/librarian/readers", "/librarian/readers/3/lock", {})
    assert library_app.users.find_by_id(3).status.value == "LOCKED"
    post_form(client, "/librarian/readers", "/librarian/readers/3/unlock", {})
    assert library_app.users.find_by_id(3).status.value == "ACTIVE"


def test_unknown_reader_action_gets_404(client):
    signin(client, "librarian@library.test")
    response = post_form(client, "/librarian/readers",
                         "/librarian/readers/3/delete", {})
    assert response.status_code == 404


# --- Administrator screens ------------------------------------------------
def test_administrator_creates_a_librarian_account(client, library_app):
    signin(client, "admin@library.test")
    response = post_form(client, "/admin/librarians", "/admin/librarians", {
        "full_name": "Le Thi Thu", "student_id": "STF-0100",
        "email": "thu@library.test", "phone": "0987654321",
        "password": "Staff1234",
    })
    assert "created for Le Thi Thu" in response.get_data(as_text=True)
    saved = library_app.users.find_by_email("thu@library.test")
    assert saved.role.value == "LIBRARIAN"
    assert saved.status.value == "ACTIVE"

    other = library_app.flask.test_client()
    assert signin(other, "thu@library.test", "Staff1234").status_code == 302


def test_administrator_edits_a_librarian(client, library_app):
    signin(client, "admin@library.test")
    response = post_form(client, "/admin/librarians/2/edit",
                         "/admin/librarians/2/edit", {
                             "full_name": "Tran Thi Mai",
                             "student_id": "STF-0002",
                             "email": "librarian@library.test",
                             "phone": "0900000002",
                         })
    assert "information updated" in response.get_data(as_text=True)
    assert library_app.users.find_by_id(2).full_name == "Tran Thi Mai"


def test_administrator_locks_a_librarian_out(client, library_app):
    signin(client, "admin@library.test")
    response = post_form(client, "/admin/librarians",
                         "/admin/librarians/2/lock", {})
    assert "locked" in response.get_data(as_text=True)
    assert library_app.users.find_by_id(2).status.value == "LOCKED"

    other = library_app.flask.test_client()
    response = signin(other, "librarian@library.test")
    assert "account is locked" in response.get_data(as_text=True)


def test_administrator_changes_the_rules(client, library_app):
    signin(client, "admin@library.test")
    response = post_form(client, "/admin/rules", "/admin/rules", {
        "MAX_BOOKS": "8", "MAX_DAYS": "21", "MAX_RENEW": "2",
        "HOLD_DAYS": "4", "DAILY_FINE": "7000",
    })
    assert "rules saved" in response.get_data(as_text=True)
    assert library_app.rule_service.current_rules().max_books == 8
    page = client.get("/policies").get_data(as_text=True)
    assert "Up to 8 books" in page
    assert "7,000 VND per day" in page


def test_invalid_rule_is_not_saved(client, library_app):
    signin(client, "admin@library.test")
    response = post_form(client, "/admin/rules", "/admin/rules", {
        "MAX_BOOKS": "0", "MAX_DAYS": "21", "MAX_RENEW": "2",
        "HOLD_DAYS": "4", "DAILY_FINE": "7000",
    })
    assert response.status_code == 400
    assert "whole number" in response.get_data(as_text=True)
    assert library_app.rule_service.current_rules().max_books == 5


# --- CSRF -----------------------------------------------------------------
def test_post_without_csrf_token_is_rejected(client):
    response = client.post("/signin", data={
        "email": "reader@library.test", "password": PASSWORD})
    assert response.status_code == 400
    assert "Form Expired" in response.get_data(as_text=True)


def test_post_with_wrong_csrf_token_is_rejected(client):
    client.get("/signin")
    response = client.post("/signin", data={
        "csrf_token": "wrong", "email": "reader@library.test",
        "password": PASSWORD})
    assert response.status_code == 400


def test_header_shows_role_links(client):
    signin(client, "admin@library.test")
    page = client.get("/").get_data(as_text=True)
    assert "Librarians" in page
    assert "Rules" in page
