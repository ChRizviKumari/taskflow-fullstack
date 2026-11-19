from conftest import add_task


def cols(board):
    return [c["id"] for c in board["columns"]]


def test_create_task_defaults_and_positions(alice, board):
    todo = cols(board)[0]
    a, b = add_task(alice, todo, "a"), add_task(alice, todo, "b")
    assert (a["position"], b["position"]) == (0, 1)
    assert a["version"] == 1 and a["priority"] == "medium" and a["description"] == ""


def test_create_task_validation_and_ownership(alice, bob, board):
    todo = cols(board)[0]
    assert alice.post(f"/api/columns/{todo}/tasks", {"title": ""}).status_code == 422
    assert alice.post(f"/api/columns/{todo}/tasks", {"title": "x", "priority": "urgent"}).status_code == 422
    assert bob.post(f"/api/columns/{todo}/tasks", {"title": "x"}).status_code == 404


def test_patch_bumps_version(alice, board):
    t = add_task(alice, cols(board)[0])
    r = alice.patch(f"/api/tasks/{t['id']}", {"version": 1, "title": "New", "priority": "high"})
    got = r.get_json()["task"]
    assert r.status_code == 200 and got["version"] == 2 and got["title"] == "New" and got["priority"] == "high"


def test_stale_version_returns_409_with_current_state(alice, board):
    t = add_task(alice, cols(board)[0])
    alice.patch(f"/api/tasks/{t['id']}", {"version": 1, "title": "first"})
    r = alice.patch(f"/api/tasks/{t['id']}", {"version": 1, "title": "second"})
    err = r.get_json()["error"]
    assert r.status_code == 409 and err["code"] == "version_conflict"
    assert err["details"]["current_version"] == 2 and err["details"]["current"]["title"] == "first"
    # the losing write must not have been applied
    assert alice.get(f"/api/tasks/{t['id']}").get_json()["task"]["title"] == "first"


def test_patch_requires_version_and_a_change(alice, board):
    t = add_task(alice, cols(board)[0])
    assert alice.patch(f"/api/tasks/{t['id']}", {"title": "x"}).status_code == 422
    assert alice.patch(f"/api/tasks/{t['id']}", {"version": 1}).status_code == 422


def test_move_between_columns_keeps_positions_contiguous(alice, board):
    todo, doing, _ = cols(board)
    a, b, c = (add_task(alice, todo, n) for n in "abc")
    d = add_task(alice, doing, "d")
    r = alice.patch(f"/api/tasks/{b['id']}", {"version": 1, "column_id": doing, "position": 0})
    moved = r.get_json()["task"]
    assert moved["column_id"] == doing and moved["position"] == 0
    tasks = alice.get(f"/api/boards/{board['id']}/tasks").get_json()["items"]
    layout = [(t["title"], t["column_id"], t["position"]) for t in tasks]
    assert layout == [("a", todo, 0), ("c", todo, 1), ("b", doing, 0), ("d", doing, 1)]


def test_reorder_within_column(alice, board):
    todo = cols(board)[0]
    a, b, c = (add_task(alice, todo, n) for n in "abc")
    alice.patch(f"/api/tasks/{c['id']}", {"version": 1, "position": 0})
    titles = [t["title"] for t in alice.get(f"/api/boards/{board['id']}/tasks").get_json()["items"]]
    assert titles == ["c", "a", "b"]


def test_position_is_clamped(alice, board):
    todo = cols(board)[0]
    a, b = add_task(alice, todo, "a"), add_task(alice, todo, "b")
    r = alice.patch(f"/api/tasks/{a['id']}", {"version": 1, "position": 99})
    assert r.get_json()["task"]["position"] == 1


def test_cannot_move_to_column_of_another_board(alice, board):
    other = alice.post("/api/boards", {"name": "Other"}).get_json()["board"]
    t = add_task(alice, cols(board)[0])
    r = alice.patch(f"/api/tasks/{t['id']}", {"version": 1, "column_id": other["columns"][0]["id"]})
    assert r.status_code == 422
    assert r.get_json()["error"]["details"][0]["field"] == "column_id"


def test_task_ownership_enforced(alice, bob, board):
    t = add_task(alice, cols(board)[0])
    assert bob.get(f"/api/tasks/{t['id']}").status_code == 404
    assert bob.patch(f"/api/tasks/{t['id']}", {"version": 1, "title": "x"}).status_code == 404
    assert bob.delete(f"/api/tasks/{t['id']}").status_code == 404


def test_delete_task_closes_gap(alice, board):
    todo = cols(board)[0]
    a, b, c = (add_task(alice, todo, n) for n in "abc")
    assert alice.delete(f"/api/tasks/{a['id']}").status_code == 204
    items = alice.get(f"/api/boards/{board['id']}/tasks").get_json()["items"]
    assert [(t["title"], t["position"]) for t in items] == [("b", 0), ("c", 1)]


def test_delete_column_removes_its_tasks(alice, board):
    todo = cols(board)[0]
    add_task(alice, todo)
    alice.delete(f"/api/columns/{todo}")
    assert alice.get(f"/api/boards/{board['id']}/tasks").get_json()["total"] == 0


def test_task_list_pagination(alice, board):
    todo = cols(board)[0]
    for i in range(7):
        add_task(alice, todo, f"t{i}")
    p = alice.get(f"/api/boards/{board['id']}/tasks?page=2&page_size=3").get_json()
    assert p["total"] == 7 and p["total_pages"] == 3
    assert [t["title"] for t in p["items"]] == ["t3", "t4", "t5"]


def test_task_filter_and_search(alice, board):
    todo, doing, _ = cols(board)
    add_task(alice, todo, "Fix login bug", priority="high")
    add_task(alice, todo, "Write docs", description="mention the LOGIN flow")
    add_task(alice, doing, "Refactor", priority="high")
    url = f"/api/boards/{board['id']}/tasks"
    assert alice.get(f"{url}?q=login").get_json()["total"] == 2  # title or description, case-insensitive
    assert alice.get(f"{url}?priority=high").get_json()["total"] == 2
    assert alice.get(f"{url}?priority=high&column_id={doing}").get_json()["total"] == 1
    assert alice.get(f"{url}?priority=nope").status_code == 422


def test_unknown_query_param_rejected(alice, board):
    assert alice.get(f"/api/boards/{board['id']}/tasks?bogus=1").status_code == 422
