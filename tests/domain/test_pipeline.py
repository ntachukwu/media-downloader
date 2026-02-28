"""
Pipeline tests — unit tests for build_pipeline.

All tests use plain Python functions as steps; no ffmpeg required.
"""

from pathlib import Path

from domain.pipeline import build_pipeline


class TestBuildPipeline:
    def test_empty_steps_returns_input_unchanged(self, tmp_path: Path) -> None:
        path = tmp_path / "file.txt"
        path.touch()
        assert build_pipeline([])(path) == path

    def test_single_step_is_applied(self, tmp_path: Path) -> None:
        original = tmp_path / "a.txt"
        redirected = tmp_path / "b.txt"
        original.touch()
        redirected.touch()

        def redirect(p: Path) -> Path:
            return redirected

        assert build_pipeline([redirect])(original) == redirected

    def test_steps_run_in_list_order(self, tmp_path: Path) -> None:
        order: list[str] = []

        def step_a(p: Path) -> Path:
            order.append("a")
            return p

        def step_b(p: Path) -> Path:
            order.append("b")
            return p

        path = tmp_path / "file.txt"
        path.touch()
        build_pipeline([step_a, step_b])(path)
        assert order == ["a", "b"]

    def test_each_step_receives_the_output_of_the_previous(self, tmp_path: Path) -> None:
        first = tmp_path / "first.txt"
        second = tmp_path / "second.txt"
        third = tmp_path / "third.txt"
        first.touch()
        second.touch()
        third.touch()

        received: list[Path] = []

        def to_second(p: Path) -> Path:
            return second

        def record_and_forward(p: Path) -> Path:
            received.append(p)
            return third

        result = build_pipeline([to_second, record_and_forward])(first)
        assert received == [second]
        assert result == third

    def test_three_steps_run_in_order_and_chain_correctly(self, tmp_path: Path) -> None:
        a = tmp_path / "a.txt"
        b = tmp_path / "b.txt"
        c = tmp_path / "c.txt"
        for f in (a, b, c):
            f.touch()

        result = build_pipeline([lambda _: b, lambda _: c, lambda p: p])(a)
        assert result == c
