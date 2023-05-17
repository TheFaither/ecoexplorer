"""
# SuPerBase Explorer

A visualizer for SuPerBase _by Daniele Liprandi_
"""

import streamlit as st
import plotly.express as px
from sqlalchemy import create_engine
import os
import datetime
import pandas as pd

full_path = os.path.join(".", "tempDir")
os.makedirs(full_path, exist_ok=True)

conn = st.experimental_connection("local_db", type="sql", url="sqlite:///")
engine = create_engine(url="sqlite:///")


def save_uploaded_file(uploadedfile):
    with open(os.path.join("tempDir", uploadedfile.name), "wb") as f:
        f.write(uploadedfile.getbuffer())
    return st.sidebar.success("Open file :{} in tempDir".format(uploadedfile.name))


datafile = st.sidebar.file_uploader("Upload database")
if datafile is not None:
    file_details = {"FileName": datafile.name, "FileType": datafile.type}
    # Apply Function here
    save_uploaded_file(datafile)
    st.cache_data.clear()
    conn = st.experimental_connection(
        "local_db", type="sql", url="sqlite:///tempDir/" + datafile.name
    )


dfi = conn.query("select * from investigator")
dfs = conn.query("select * from sample")
dft1 = conn.query("select * from silktrait NATURAL JOIN trait")
dft2 = conn.query(
    "select * from individualtrait NATURAL JOIN trait INNER JOIN sample ON sample.id = trait.samples_id"
)
dft2[["uploaddate", "collectiondate"]] = dft2[["uploaddate", "collectiondate"]].apply(
    pd.to_datetime
)
dfe = conn.query("select * from experiment")
dff = [dfi, dfs, dft1, dft2, dfe]
tabs = st.tabs(
    ["Investigator", "Sample", "Silk Trait", "Individual Trait", "Experiment"]
)

for dfnum, df in enumerate(dff):
    with tabs[dfnum]:
        st.dataframe(df)

with tabs[1]:
    # st.bar_chart(
    #    data=dfs, x="id", y="species", width=0, height=0, use_container_width=True
    # )
    # st.divider()
    st.map(data=dfs)
    st.divider()
    # fighist = px.histogram(dfs, x="species", histfunc="count")
    # st.plotly_chart(fighist)
    # st.divider()
    # ------------------------------ collection tree ----------------------------- #
    figcollectiontree = px.treemap(
        dfs,
        path=[px.Constant("all"), "family", "genus", "species"],
    )
    figcollectiontree.update_traces(root_color="lightgrey")
    figcollectiontree.update_layout(margin=dict(t=50, l=25, r=25, b=25))
    figcollectiontree.update_traces(marker=dict(cornerradius=20))
    st.plotly_chart(figcollectiontree)
    st.divider()
    # ------------------------------ Parent tree ----------------------------- #
    optiongroupby = st.selectbox(
        "Color by",
        ["family", "genus", "species", "sample_class", "responsible_id"],
        index=3,
    )
    figparenttree = px.treemap(
        dfs,
        names="id",
        parents="parent_id",
        color=optiongroupby,
        hover_data=["nomenclature", "sample_class"],
        labels=["id", "sample_class"],
    )
    figparenttree.update_traces(root_color="lightgrey")
    figparenttree.update_layout(margin=dict(t=50, l=25, r=25, b=25))
    figparenttree.update_traces(marker=dict(cornerradius=20))
    figparenttree.update_traces(
        textinfo="label+value+percent parent+percent entry+percent root"
    )
    st.plotly_chart(figparenttree)
    st.divider()

with tabs[2]:
    st.write("Diameters chart")
    # -------------------------------- line chart -------------------------------- #
    st.line_chart(
        data=dft1, x="id", y="diameter", width=0, height=0, use_container_width=True
    )
    # --------------------------------- histogram -------------------------------- #
    figtraithist = px.histogram(dft1, x="diameter")
    st.plotly_chart(figtraithist)

with tabs[3]:
    st.write("Weight chart")
    # --------------------------------- histogram -------------------------------- #
    optiongroupby = st.selectbox(
        "Color by", ["family", "genus", "species", "samples_id"], index=0
    )
    optionsselect = st.multiselect(
        "Filter", dfs.nomenclature.unique(), dfs.nomenclature.unique()
    )
    startdate = st.slider(
        "Show only data uploaded after this date",
        min_value=datetime.datetime.fromisocalendar(2020, 1, 1),
        max_value=datetime.datetime.fromisocalendar(2024, 1, 1),
        value=datetime.datetime.fromisocalendar(2022, 1, 1),
    )

    figtraithist = px.histogram(
        dft2.query("nomenclature in @optionsselect").query("uploaddate > @startdate"),
        x="weight",
        nbins=20,
        color=optiongroupby,
    )
    st.plotly_chart(figtraithist)
# st.experimental_data_editor(
#     dfs,
#     width=None,
#     height=None,
#     use_container_width=False,
#     num_rows="dynamic",
#     on_change=dfs.to_sql("sample", engine, if_exists='replace'),
# )
