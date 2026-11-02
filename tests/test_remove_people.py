"""Removing a person from the workspace, or only their contact record."""
import pytest

from test_network_http import request, running_server
from test_workspace_backup import ORCID_A, ORCID_B, bio, populated, work


def people(state):
    return {person["id"] for person in state["people"]}


def test_removing_a_person_keeps_outputs_someone_else_lists(tmp_path):
    store, group_id = populated(tmp_path / "net.sqlite3")
    store.tag_contacts([ORCID_B], add=["FENS 2026"])
    store.remove_person(ORCID_B)
    state = store.state()
    group = next(g for g in state["groups"] if g["id"] == group_id)
    shared = next(w for w in state["works"] if w["id"] == "doi:10.1/shared")
    assert ORCID_B not in people(state) and ORCID_A in people(state)
    assert ORCID_B not in state["contacts"]
    assert group["member_ids"] == [ORCID_A]
    assert group["requests"][0]["owner_id"] is None
    assert shared["people_ids"] == [ORCID_A] and shared["saved"]
    assert group["selected_work_ids"] == ["doi:10.1/shared"]


def test_removing_a_person_drops_their_own_outputs_and_group_details(tmp_path):
    store, group_id = populated(tmp_path / "net.sqlite3")
    solo = next(w["id"] for w in store.state()["works"] if w["title"] == "Solo note")
    store.save(solo, True)
    store.remove_person(ORCID_A)
    state = store.state()
    group = next(g for g in state["groups"] if g["id"] == group_id)
    assert solo not in {w["id"] for w in state["works"]}
    assert group["member_ids"] == [ORCID_B] and group["member_details"] == {}
    assert next(w for w in state["works"] if w["id"] == "doi:10.1/shared")["people_ids"] == [ORCID_B]
    assert group["requests"][0]["owner_id"] == ORCID_B


def test_removing_everyone_on_an_output_removes_it_from_saved_and_projects(tmp_path):
    store, group_id = populated(tmp_path / "net.sqlite3")
    store.remove_person(ORCID_A)
    store.remove_person(ORCID_B)
    state = store.state()
    group = next(g for g in state["groups"] if g["id"] == group_id)
    assert "doi:10.1/shared" not in {w["id"] for w in state["works"]}
    assert group["member_ids"] == [] and group["selected_work_ids"] == []
    assert any(p["demo"] for p in state["people"])


def test_a_removed_person_can_be_imported_again(tmp_path):
    store, _ = populated(tmp_path / "net.sqlite3")
    store.follow(ORCID_B, False)
    store.remove_person(ORCID_B)
    store.import_biosketch(bio(ORCID_B, "Ben Example", [work(7, "10.1/shared", "Shared paper")]))
    person = next(p for p in store.state()["people"] if p["id"] == ORCID_B)
    assert person["following"] is True


def test_removing_a_contact_keeps_the_person(tmp_path):
    store, group_id = populated(tmp_path / "net.sqlite3")
    store.tag_contacts([ORCID_A], add=["FENS 2026"], met_on="2026-07-08")
    store.add_contact_note(ORCID_A, "Talked about the dataset")
    store.add_contact_action(ORCID_A, "Send the protocol")
    before = store.state()
    store.remove_contact(ORCID_A)
    after = store.state()
    assert ORCID_A not in after["contacts"]
    assert after["people"] == before["people"] and after["works"] == before["works"]
    assert after["groups"] == before["groups"]
    store.remove_contact(ORCID_A)  # Already clear: nothing to do, not an error.


def test_remove_routes_over_http(tmp_path):
    with running_server(tmp_path) as server:
        request(server, "POST", "/api/demo", {})
        request(server, "POST", "/api/contacts/tags", {"person_ids": ["demo-ada"], "add": ["FENS 2026"]})
        status, state = request(server, "POST", "/api/contacts/remove", {"person_id": "demo-ada"})
        assert status == 200 and "demo-ada" not in state["contacts"] and "demo-ada" in people(state)
        status, state = request(server, "POST", "/api/people/remove", {"id": "demo-ada"})
        assert status == 200 and "demo-ada" not in people(state)
        assert all("demo-ada" not in g["member_ids"] for g in state["groups"])


@pytest.mark.parametrize("path,body", [
    ("/api/people/remove", {"id": "0000-0000-0000-0000"}),
    ("/api/people/remove", {"id": ["demo-ada"]}),
    ("/api/people/remove", {}),
    ("/api/contacts/remove", {"person_id": "nobody"}),
    ("/api/contacts/remove", {"person_id": None}),
])
def test_invalid_removals_are_rejected_without_changes(tmp_path, path, body):
    with running_server(tmp_path) as server:
        request(server, "POST", "/api/demo", {})
        before = request(server)[1]
        status, result = request(server, "POST", path, body)
        assert status == 400 and "error" in result
        assert request(server)[1] == before
