"""Staff roles and permissions (FR-ADM-02, FR-SYS-04)."""
import pytest

from business.role_service import RoleService
from common.exceptions import ValidationError
from data.repositories import StaffRoleRepository, UserRepository
from models import Administrator, Librarian, Permission, StaffRole
from web_helpers import post_form, signin, text


@pytest.fixture
def roles(database):
    return RoleService(StaffRoleRepository(database),
                       UserRepository(database))


@pytest.fixture
def admin(database):
    return UserRepository(database).find_by_id(1)


# --- Unit: StaffRole and Administrator.manage_role --------------------------
def test_role_has_only_its_permissions():
    role = StaffRole(1, "Desk", permissions={Permission.CIRCULATION})
    assert role.has("CIRCULATION")
    assert not role.has(Permission.CATALOG)


def test_librarian_without_role_has_no_permission():
    librarian = Librarian(2, "Lan", "l@x.test", "0900000002", "h")
    assert not librarian.can(Permission.CIRCULATION)


@pytest.mark.parametrize("name, codes, ok", [
    ("Desk", ["CIRCULATION"], True),
    ("AB", ["FINES"], True),                  # shortest name (boundary)
    ("A", ["FINES"], False),                  # 1 character
    ("X" * 50, ["FINES"], True),              # longest name (boundary)
    ("X" * 51, ["FINES"], False),
    ("Desk", [], False),                      # no permission
    ("Desk", ["SUPERUSER"], False),           # unknown permission
])
def test_manage_role_partitions(name, codes, ok):
    admin = Administrator(1, "Admin", "a@x.test", "0900000001", "h")
    role = StaffRole(None, "")
    if ok:
        admin.manage_role(role, name, "", codes)
        assert role.name == name
    else:
        with pytest.raises(ValueError):
            admin.manage_role(role, name, "", codes)


# --- Component: RoleService and repository ----------------------------------
def test_default_roles_are_seeded(roles):
    names = [r.name for r in roles.all_roles()]
    assert names == ["Full Librarian", "Circulation Desk",
                     "Catalog Librarian"]
    assert roles.find(1).permissions == set(Permission)


def test_create_update_and_delete_role(roles, admin):
    role = roles.save_role(admin, "Night Desk", "Evening shift",
                           ["CIRCULATION", "FINES"])
    assert roles.find(role.role_id).has(Permission.FINES)
    roles.save_role(admin, "Night Desk", "", ["CATALOG"],
                    role_id=role.role_id)
    assert roles.find(role.role_id).permissions == {Permission.CATALOG}
    roles.delete_role(admin, role.role_id)
    with pytest.raises(ValidationError):
        roles.find(role.role_id)


def test_duplicate_role_name_is_rejected(roles, admin):
    with pytest.raises(ValidationError, match="already exists"):
        roles.save_role(admin, "full librarian", "", ["FINES"])


def test_role_in_use_cannot_be_deleted(roles, admin):
    with pytest.raises(ValidationError, match="Move the Librarians"):
        roles.delete_role(admin, 1)


def test_assign_role_changes_permissions(roles, admin, database):
    roles.assign_role(admin, 2, 3)
    librarian = roles.attach(UserRepository(database).find_by_id(2))
    assert librarian.can(Permission.CATALOG)
    assert not librarian.can(Permission.CIRCULATION)


def test_only_librarians_get_a_role(roles, admin):
    with pytest.raises(ValidationError):
        roles.assign_role(admin, 3, 1)          # user 3 is a Reader


# --- System: permissions are checked on every page --------------------------
def test_catalog_librarian_only_reaches_catalog_pages(client, library_app):
    library_app.users.assign_staff_role(2, 3)   # Catalog Librarian
    signin(client, "librarian@library.test")
    assert client.get("/librarian/books").status_code == 200
    assert client.get("/librarian/inventory").status_code == 200
    for url in ["/librarian/checkout", "/librarian/checkin",
                "/librarian/readers", "/librarian/fines"]:
        assert client.get(url).status_code == 403, url
    menu = text(client.get("/librarian/books"))
    assert "Inventory" in menu and "Check Out" not in menu
    home = client.get("/librarian/")
    assert home.headers["Location"].endswith("/librarian/books")


def test_post_without_permission_is_blocked(client, library_app):
    library_app.users.assign_staff_role(2, 3)
    signin(client, "librarian@library.test")
    response = post_form(client, "/librarian/books", "/librarian/checkout",
                         {"card_code": "RD-0004", "barcode": "LIB-00061"},
                         follow_redirects=False)
    assert response.status_code == 403


def test_admin_creates_role_and_assigns_it(client, library_app):
    signin(client, "admin@library.test")
    page = post_form(client, "/admin/roles", "/admin/roles", {
        "name": "Fines Only", "description": "Cashier",
        "permissions": ["FINES"]})
    assert "Role created: Fines Only" in text(page)
    role = next(r for r in library_app.role_service.all_roles()
                if r.name == "Fines Only")
    page = post_form(client, "/admin/librarians/2/edit",
                     "/admin/librarians/2/edit", {
                         "full_name": "Tran Thi Lan",
                         "email": "librarian@library.test",
                         "phone": "0900000002", "student_id": "STF-0002",
                         "staff_role_id": str(role.role_id)})
    assert "Librarian information updated" in text(page)
    assert library_app.users.find_by_id(2).staff_role_id == role.role_id


def test_role_page_is_admin_only(client):
    signin(client, "librarian@library.test")
    assert client.get("/admin/roles").status_code == 403
