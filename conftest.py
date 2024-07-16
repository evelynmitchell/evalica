from __future__ import annotations

from itertools import product
from pathlib import Path
from typing import TYPE_CHECKING, Literal, NamedTuple, cast

import evalica
import pandas as pd
import pytest
from hypothesis import strategies as st
from hypothesis.strategies import composite

if TYPE_CHECKING:
    from _pytest.fixtures import TopRequest
    from hypothesis.strategies import DrawFn


class Example(NamedTuple):
    """A tuple holding example data."""

    xs: list[str] | pd.Series[str]
    ys: list[str] | pd.Series[str]
    ws: list[evalica.Winner] | pd.Series[evalica.Winner]  # type: ignore[type-var]


def enumerate_sizes(n: int) -> list[tuple[int, ...]]:
    return [xs for xs in product([0, 1], repeat=n) if 0 < sum(xs) < n]


@composite
def elements(
        draw: DrawFn,
        shape: Literal["good", "bad"] = "good",
) -> Example:  # type: ignore[type-var]
    length = draw(st.integers(0, 5))

    if shape == "good":
        xs = st.lists(st.text(max_size=length), min_size=length, max_size=length)
        ys = st.lists(st.text(max_size=length), min_size=length, max_size=length)
        ws = st.lists(st.sampled_from(evalica.WINNERS), min_size=length, max_size=length)
    else:
        min_x, min_y, min_z = draw(st.sampled_from(enumerate_sizes(3)))

        length_x, length_y, length_z = (1 + length) * min_x, (1 + length) * min_y, (1 + length) * min_z

        xs = st.lists(st.text(max_size=length_x), min_size=length_x, max_size=length_x)
        ys = st.lists(st.text(max_size=length_y), min_size=length_y, max_size=length_y)
        ws = st.lists(st.sampled_from(evalica.WINNERS), min_size=length_z, max_size=length_z)

    return Example(xs=draw(xs), ys=draw(ys), ws=draw(ws))


@pytest.fixture()
def simple() -> Example:
    df_simple = pd.read_csv(Path(__file__).resolve().parent / "simple.csv", dtype=str)

    xs = df_simple["left"]
    ys = df_simple["right"]
    ws = df_simple["winner"].map({
        "left": evalica.Winner.X,
        "right": evalica.Winner.Y,
        "tie": evalica.Winner.Draw,
    })

    return Example(xs=xs, ys=ys, ws=ws)


@pytest.fixture()
def simple_golden() -> pd.DataFrame:
    df_golden = pd.read_csv(Path(__file__).resolve().parent / "simple-golden.csv", dtype=str)

    df_golden["score"] = df_golden["score"].astype(float)

    return df_golden


@pytest.fixture()
def food() -> Example:
    df_food = pd.read_csv(Path(__file__).resolve().parent / "food.csv", dtype=str)

    xs = df_food["left"]
    ys = df_food["right"]
    ws = df_food["winner"].map({
        "left": evalica.Winner.X,
        "right": evalica.Winner.Y,
        "tie": evalica.Winner.Draw,
    })

    return Example(xs=xs, ys=ys, ws=ws)


@pytest.fixture()
def food_golden() -> pd.DataFrame:
    df_golden = pd.read_csv(Path(__file__).resolve().parent / "food-golden.csv", dtype=str)

    df_golden["score"] = df_golden["score"].astype(float)

    return df_golden


@pytest.fixture()
def llmfao() -> Example:
    df_llmfao = pd.read_csv("https://github.com/dustalov/llmfao/raw/master/crowd-comparisons.csv", dtype=str)

    xs = df_llmfao["left"]
    ys = df_llmfao["right"]
    ws = df_llmfao["winner"].map({
        "left": evalica.Winner.X,
        "right": evalica.Winner.Y,
        "tie": evalica.Winner.Draw,
    })

    return Example(xs=xs, ys=ys, ws=ws)


@pytest.fixture()
def llmfao_golden() -> pd.DataFrame:
    df_golden = pd.read_csv(Path(__file__).resolve().parent / "llmfao-golden.csv", dtype=str)

    df_golden["score"] = df_golden["score"].astype(float)

    return df_golden


DATASETS = frozenset(("simple", "food", "llmfao"))


@pytest.fixture()
def example(request: TopRequest, dataset: str) -> Example:
    assert dataset in DATASETS, f"unknown dataset: {dataset}"

    return cast(Example, request.getfixturevalue(dataset))


@pytest.fixture()
def example_golden(request: TopRequest, dataset: str, algorithm: str) -> pd.Series[str]:
    assert dataset in DATASETS, f"unknown dataset: {dataset}"

    df_golden = cast(pd.DataFrame, request.getfixturevalue(f"{dataset}_golden"))

    df_slice = df_golden[df_golden["algorithm"] == algorithm][["item", "score"]].set_index("item")

    series = cast("pd.Series[str]", df_slice.squeeze())
    series.index.name = None
    series.name = algorithm

    return series
