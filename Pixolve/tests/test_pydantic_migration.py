from backend.app.schemas.lobby import PlayerInLobby, LobbyOut
from backend.app.schemas.game import RevealStep, RoundState, GameState
from backend.app.schemas.user import UserCreate, UserOut
from backend.app.schemas.score import Score
from backend.app.schemas.category import Category
import os


def test_models_have_model_dump_and_return_expected_keys():
    p = PlayerInLobby(id="p1", username="p1", display_name="P One")
    pd = p.model_dump()
    assert isinstance(pd, dict)
    assert pd["id"] == "p1"

    rs = RevealStep(step_index=0, pixelation=32, time_offset=0.0)
    rds = rs.model_dump()
    assert rds["pixelation"] == 32

    rr = RoundState(round_index=0, image_id="img0", reveal_steps=[rs], duration_secs=20)
    rrd = rr.model_dump()
    assert rrd["round_index"] == 0

    gs = GameState(id="g1", lobby_id="l1", round_index=0, rounds=[rr], players=["p1"], finished=False)
    gsd = gs.model_dump()
    assert gsd["id"] == "g1"

    u = UserCreate(username="u1", password="pw")
    ud = u.model_dump()
    assert ud["username"] == "u1"

    so = Score(player_id="p1", points=10)
    sod = so.model_dump()
    assert sod["points"] == 10

    c = Category(id="c1", name="cats", description="desc")
    cd = c.model_dump()
    assert cd["id"] == "c1"


def test_no_legacy_dict_calls_in_repo():
    # scan repo for '.dict(' usage
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    found = []
    for dirpath, dirnames, filenames in os.walk(repo_root):
        # skip virtualenvs, .git, node_modules
        if any(x in dirpath for x in (".git", "venv", "env", "node_modules")):
            continue
        for fn in filenames:
            if not fn.endswith(('.py', '.md')):
                continue
            fp = os.path.join(dirpath, fn)
            # skip this test file which intentionally contains the string in comments
            if os.path.abspath(fp) == os.path.abspath(__file__):
                continue
            with open(fp, 'r', encoding='utf-8') as f:
                txt = f.read()
            if '.dict(' in txt:
                found.append(fp)
    assert len(found) == 0, f"Found legacy .dict() usages in files: {found}"
