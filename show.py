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

COLORS = {
    col2020: "#00C49A",
    colprev: "#FB8F67",
    change: "#156064",
    smoothchange: "#F8E16C",
}


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
    df_out[change] = df_out[col2020] / df_out[colprev] - 1

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
        line_color=COLORS.get(col),
        hoverlabel=dict(
            bgcolor="white",
            bordercolor=COLORS.get(col),
            font=dict(
                family="Sans Serif",
                color="#474747",
            ),
        ),
    )


def plot(df):
    figs = [go.Figure() for _ in range(2)]
    allcols = ([col2020, colprev], (change, smoothchange))
    titles = ("Energy consumption", "Change in energy consumption")
    yaxis_titles = ("Consumption (GWh)", "Change in consumpt.")
    annotation_placements = ("bottom", "top")
    for fig, cols, title, yaxis_title, annotation_placement in zip(
        figs, allcols, titles, yaxis_titles, annotation_placements
    ):

        for col in cols:
            fig.add_trace(get_trace(df, col))

        fig.update_layout(
            title=title,
            xaxis_title="Date",
            yaxis_title=yaxis_title,
            hovermode="x",
            hoverdistance=-1,
            spikedistance=-1,
            yaxis_range=[-0.2, 17],
            autosize=True,
            font=dict(family="Open Sans", size=16, color="gray"),
            template="ggplot2",
            legend=dict(
                x=0,
                y=0.7,
                traceorder="normal",
                font=dict(
                    size=12,
                ),
            ),
        )
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

        fig.add_vrect(
            x0="2020-03-28",
            x1="2020-04-15",
            fillcolor="mediumslateblue",
            annotation=go.layout.Annotation(text="Uusimaa lockdown", textangle=270),
            annotation_position=f"inside {annotation_placement} right",
            opacity=0.08,
            line_width=0,
        )
        fig.add_vrect(
            x0="2020-03-17",
            x1="2020-06-15",
            fillcolor="purple",
            annotation=go.layout.Annotation(text="Valmiuslaki", textangle=270),
            annotation_position=f"inside {annotation_placement} left",
            opacity=0.05,
            line_width=0,
        )
    figs[1].update_yaxes(tickformat="+%", range=[-0.14, 0.14])

    for i, fig in enumerate(figs):
        plotly.offline.plot(
            fig,
            filename=f"plot{i+1}.html",
            auto_open=False,
            include_plotlyjs=i == 0,
        )


if __name__ == "__main__":
    df = get_data()
    plot(df)
    df.to_csv("helen2020.csv")
