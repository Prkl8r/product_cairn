from cairn_cli import rank


def write_config(tmp_path, text):
    (tmp_path / ".cairn").mkdir(exist_ok=True)
    (tmp_path / ".cairn/config.yaml").write_text(text)


def ids(tmp_path, metas):
    return [t["id"] for t in rank.annotate(tmp_path, [{"id": i} for i in metas], metas)]


def test_default_levels_sort_high_first_and_unset_last(tmp_path):
    metas = {"T1": {"priority": "Low"}, "T2": {}, "T3": {"priority": "high"}, "T4": {"priority": "Medium"}}
    assert ids(tmp_path, metas) == ["T3", "T4", "T1", "T2"]


def test_rice_scores_and_effort_defaults_from_size(tmp_path):
    write_config(tmp_path, "priority: {scheme: rice}\nsize: {scheme: tshirt}\n")
    metas = {"A": {"priority": {"reach": 100, "impact": 2, "confidence": 0.5, "effort": 4}},
             "B": {"priority": {"reach": 100, "impact": 2, "confidence": 0.5}, "size": "XS"}}
    out = {t["id"]: t["priority_score"] for t in rank.annotate(tmp_path, [{"id": "A"}, {"id": "B"}], metas)}
    assert out == {"A": 25.0, "B": 100.0}


def test_custom_formula_and_levels(tmp_path):
    write_config(tmp_path, "priority:\n  scheme: {fields: [value, cost], formula: 'value / (cost + 1)'}\n"
                           "size:\n  scheme: {levels: [Tiny, Huge]}\n")
    metas = {"A": {"priority": {"value": 10, "cost": 1}}, "B": {"priority": {"value": 9, "cost": 0}}}
    assert ids(tmp_path, metas) == ["B", "A"]
    assert rank.problems(tmp_path, {"size": "Medium"}) == ["size `Medium` isn't Tiny, Huge"]


def test_problems_flag_bad_values(tmp_path):
    assert rank.problems(tmp_path, {"priority": "Urgent", "size": "Small"}) == [
        "priority `Urgent` isn't one of High, Medium, Low"]
    write_config(tmp_path, "priority: {scheme: ice}\nsize: {scheme: days}\n")
    assert rank.problems(tmp_path, {"priority": {"impact": 3}, "size": -1,
                                    "planned_specs": [{"key": "core", "size": "L"}]}) == [
        "priority is missing confidence, ease", "size `-1` isn't a positive number of days",
        "planned Spec `core`: size `L` isn't a positive number of days"]


def test_formula_rejects_anything_but_arithmetic(tmp_path):
    write_config(tmp_path, "priority:\n  scheme: {fields: [a], formula: '__import__(\"os\")'}\n")
    assert "formula" in rank.problems(tmp_path, {"priority": {"a": 1}})[0]
