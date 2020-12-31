import datetime as dt
import math

import pandas as pd
from scipy.interpolate import interp1d
from scipy.signal import savgol_filter

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.offline
import numpy as np

import csaps

colprev = "2015-2019"
col2020 = "2020"
change = "change"
smoothchange = "smoothed change"
yearcols = [col2020, colprev]
changecols = [change, smoothchange]


def get_data():
    df = pd.read_csv("helen2020-raw.csv")
    min_ = math.ceil(df["x"].min())
    max_ = math.floor(df["x"].max())

    # interpolate data
    d = dict()
    x_new = range(min_, max_ + 1)
    for col in yearcols:
        f = interp1d(x=df["x"], y=df[col])
        d[col] = f(x_new)

    df_out = pd.DataFrame(d)

    # Not 100% exact, since conversion from
    # day of year to date depends on the year.
    timestamps = []
    for day in x_new:
        timestamps.append(dt.datetime.strptime(col2020 + "-" + str(day), "%Y-%j"))
    df_out.index = timestamps

    # Relative change in consumption
    df_out[change] = 1 - df_out[col2020] / df_out[colprev]

    # Smoothed relative change
    df_out[smoothchange] = csaps.csaps(x_new, df_out[change], x_new, smooth=0.0001)

    return df_out


def _get_template(col):
    if col in yearcols:
        return (
            f"<b>{col}</b><br>"
            + "<b>Date</b>: {date}<br>"
            + "<b>Consumption</b>: {y:.2f} GWh"
        )
    return "<b>Date</b>: {date}<br>" + f"<b>{col}</b>" + ": {y:+.2%}"


def _get_hovertext_row(template, ts, row, col):

    text = template.format(date=ts.strftime("%B %d"), y=row[col])
    if col == col2020:
        val = row[change]
        text += f"<br><b>Change:</b> {val:+.1%}"
    return text


def create_hovertext(df, col):
    template = _get_template(col)
    hovertext = []
    for ts, row in df.iterrows():
        hovertext.append(_get_hovertext_row(template, ts, row, col))
    return hovertext


def get_trace(df, col):

    hovertext = create_hovertext(df, col)
    return go.Scatter(
        x=df.index,
        y=df[col],
        name=col,
        hoverinfo="text",
        text=hovertext,
        fill="tozeroy" if col in changecols else None,
    )


def plot(df):
    fig = make_subplots(
        rows=2,
        cols=1,
        vertical_spacing=0.07,
        subplot_titles=(
            "Energy consumption",
            "Change in energy consumption",
        ),
        x_title="Date",
        row_titles=("Consumption (GWh)", "Change in consumpt."),
    )

    rowmap = {col2020: 1, colprev: 1, change: 2, smoothchange: 2}
    for col, row in rowmap.items():
        fig.add_trace(get_trace(df, col), row=row, col=1)

    fig.update_layout(
        title="Helen data",
        hovermode="x",
        hoverdistance=-1,
        spikedistance=-1,
        yaxis_range=[-0.2, 17],
        autosize=False,
        width=1000,
        height=1200,
        font=dict(family="Open Sans", size=16, color="gray"),
        template="ggplot2",
    )
    fig.update_yaxes(tickformat="+%", range=[-0.14, 0.14], row=2, col=1)
    fig.update_xaxes(
        showgrid=True,
        tickformat="%b",  # months
        ticklabelmode="period",  # one month boxes
        dtick="M1",
        spikemode="across",
        spikesnap="cursor",
        spikedash="solid",
        spikethickness=1,
        spikecolor="#2b2b2b",
    )
    plotly.offline.plot(fig, filename="plot")


if __name__ == "__main__":
    df = get_data()
    plot(df)
    df.to_csv("helen2020.csv")
