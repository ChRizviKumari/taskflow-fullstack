from conftest import add_task


def test_boards_require_auth(client):
    assert client.get("/api/boards").status_code == 401


def test_create_board_has_default_columns(board):
    assert [c["name"] for c in board["columns"]] == ["To Do", "In Progress", "Done"]
    assert [c["position"] for c in board["columns"]] == [0, 1, 2]


def test_board_validation(alice):
    r = alice.post("/api/boards", {"name": "  "})
    assert r.status_code == 422


def test_list_boards_paginates_and_searches(alice):
    for i in range(5):
        alice.post("/api/boards", {"name": f"Board {i}"})
    alice.post("/api/boards", {"name": "100%_special"})
    page = alice.get("/api/boards?page=2&page_size=2").get_json()
    assert page["total"] == 6 and page["total_pages"] == 3 and len(page["items"]) == 2
    found = alice.get("/api/boards?q=Board 3").get_json()
    assert [b["name"] for b in found["items"]] == ["Board 3"]
    # wildcard characters are matched literally
    assert alice.get("/api/boards?q=%25").get_json()["total"] == 1
    assert alice.get("/api/boards?q=_").get_json()["total"] == 1


def test_page_size_is_capped(alice):
    r = alice.get("/api/boards?page_size=1000")
    assert r.status_code == 422


def test_other_users_boards_are_invisible(alice, bob, board):
    assert bob.get(f"/api/boards/{board['id']}").status_code == 404
    assert bob.patch(f"/api/boards/{board['id']}", {"name": "x"}).status_code == 404
    assert bob.delete(f"/api/boards/{board['id']}").status_code == 404
    assert bob.get(f"/api/boards/{board['id']}/tasks").status_code == 404
    assert bob.get("/api/boards").get_json()["total"] == 0


def test_rename_and_delete_board(alice, board):
    r = alice.patch(f"/api/boards/{board['id']}", {"name": "Renamed"})
    assert r.get_json()["board"]["name"] == "Renamed"
    assert alice.delete(f"/api/boards/{board['id']}").status_code == 204
    assert alice.get(f"/api/boards/{board['id']}").status_code == 404


def test_delete_board_cascades_tasks(app, alice, board):
    import sqlite3
    add_task(alice, board["columns"][0]["id"])
    alice.delete(f"/api/boards/{board['id']}")
    conn = sqlite3.connect(app.config["DATABASE"])
    assert conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM columns").fetchone()[0] == 0


def test_column_crud_and_ownership(alice, bob, board):
    r = alice.post(f"/api/boards/{board['id']}/columns", {"name": "QA"})
    col = r.get_json()["column"]
    assert r.status_code == 201 and col["position"] == 3
    assert bob.patch(f"/api/columns/{col['id']}", {"name": "hax"}).status_code == 404
    assert alice.patch(f"/api/columns/{col['id']}", {"name": "Review"}).get_json()["column"]["name"] == "Review"
    assert alice.delete(f"/api/columns/{col['id']}").status_code == 204
    assert len(alice.get(f"/api/boards/{board['id']}").get_json()["board"]["columns"]) == 3
