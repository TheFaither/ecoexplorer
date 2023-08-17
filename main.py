"""
# SuPerBase Explorer

A visualizer for SuPerBase _by Daniele Liprandi_
"""

import streamlit as st
import plotly.express as px

# from sqlalchemy import create_engine
import os
import datetime
import pandas as pd
import numpy as np
import pygwalker as pyg
import streamlit.components.v1 as components
from converter import getattributesandmeasureformultiplefiles

full_path = os.path.join(".", "tempDir")
os.makedirs(full_path, exist_ok=True)


conn = st.experimental_connection("local_db", type="sql", url="sqlite:///demoframe.sql")
# engine = create_engine(url="sqlite:///demoDir/evonest.sql")


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
dfsindividuals = conn.query("select * from sample NATURAL JOIN individualsample")
dft1 = conn.query(
    "select silktrait.id, trait.samples_id, silktrait.silk_type, sample.tag as sample_tag, silktrait.diameter, silktrait.diameter_std, silktrait.diameter_listvals, trait.uploaddate, sample.collectiondate, trait.responsible_id, trait.tag as trait_tag, sample.family, sample.genus, sample.species, sample.nomenclature, sample.parent_id from silktrait NATURAL JOIN trait INNER JOIN sample ON trait.samples_id = sample.id"
)
dft2 = conn.query(
    "select individualtrait.id, trait.samples_id, individualtrait.weight, sample.tag as sample_tag, trait.uploaddate, sample.collectiondate, trait.responsible_id, trait.tag as trait_tag, sample.family, sample.genus, sample.species, sample.nomenclature, sample.parent_id from individualtrait NATURAL JOIN trait INNER JOIN sample ON sample.id = trait.samples_id"
)
try:
    dftensile = conn.query("select * from tensileexperiment NATURAL JOIN experiment")
except:
    ...
try:
    dft1[["uploaddate", "collectiondate"]] = dft1[
        ["uploaddate", "collectiondate"]
    ].apply(pd.to_datetime)
except Exception as e:
    pass
try:
    dft2[["uploaddate", "collectiondate"]] = dft2[
        ["uploaddate", "collectiondate"]
    ].apply(pd.to_datetime)
except Exception as e:
    pass
dfe = conn.query("select * from experiment")
dff = [dfi, dfs, dft1, dft2, dfe]
tabs = st.tabs(
    [
        "Home",
        "Investigator",
        "Sample",
        "Silk Trait",
        "Individual Trait",
        "Experiment",
        "Chart Generator",
        "Tensile test converter",
    ]
)

for dfnum, df in enumerate(dff):
    with tabs[dfnum + 1]:
        try:
            st.dataframe(df)
        except Exception as e:
            st.write(e)

with tabs[0]:
    st.write("# EvoNEST Explorer\n" "by _Daniele Liprandi_\n")
    st.write(
        "A demo database is initially displayed. Please upload a database using the left sidebar"
    )
    st.write("Visit the Silk Trait tab to see an analysis demonstration.")

# ---------------------------------------------------------------------------- #
#                                  sample page                                 #
# ---------------------------------------------------------------------------- #
with tabs[2]:
    with st.expander("Animals", expanded=False):
        st.write(dfsindividuals)
    # ------------------------------------ map ----------------------------------- #
    dfsmap = dfs.dropna(subset="latitude")
    st.map(data=dfsmap)
    st.divider()
    # --------------------------------- Histogram -------------------------------- #
    fighist = px.histogram(dfs, x="species", histfunc="count")
    st.plotly_chart(fighist)
    st.divider()
    # ------------------------------ collection tree ----------------------------- #
    st.write("## Taxonomic Sample Tree Map")
    figcollectiontree = px.treemap(
        dfs,
        path=[px.Constant("all"), "family", "genus", "species"],
    )
    figcollectiontree.update_layout(margin=dict(t=50, l=25, r=25, b=25))
    figcollectiontree.update_traces(marker=dict(cornerradius=20))
    st.plotly_chart(figcollectiontree)
    st.divider()
    st.write("## Tagged sample tree map")
    with st.expander("Filters", expanded=False):
        speciestagfilter = st.multiselect(
            "Tags", dfs.tag.unique(), dfs.tag.unique(), key="tagfilter1"
        )
    # FIXME Tag None is considered, but it shouldn't. The best thing would be to clean all the nones in explorer
    figcollectiontreetag = px.treemap(
        dfs.query("tag in @speciestagfilter").query("tag.notnull()"),
        path=[px.Constant("all"), "family", "genus", "species", "tag"],
    )
    figcollectiontreetag.update_layout(margin=dict(t=50, l=25, r=25, b=25))
    figcollectiontreetag.update_traces(marker=dict(cornerradius=20))
    st.plotly_chart(figcollectiontreetag)
    st.divider()
    # # ------------------------------ Parent tree ----------------------------- #
    # optiongroupby = st.selectbox(
    #     "Color by",
    #     ["family", "genus", "species", "sample_class", "responsible_id"],
    #     key="optiongroupby_parent",
    #     index=3,
    # )
    # figparenttree = px.treemap(
    #     dfs,
    #     names="id",
    #     parents="parent_id",
    #     color=optiongroupby,
    #     hover_data=["nomenclature", "sample_class"],
    #     labels=["id", "sample_class"],
    # )
    # figparenttree.update_layout(margin=dict(t=50, l=25, r=25, b=25))
    # figparenttree.update_traces(marker=dict(cornerradius=20))
    # figparenttree.update_traces(
    #     textinfo="label+value+percent parent+percent entry+percent root"
    # )
    # st.plotly_chart(figparenttree)
    # st.divider()

# ---------------------------------------------------------------------------- #
#                                  silk traits                                 #
# ---------------------------------------------------------------------------- #
with tabs[3]:
    st.write("## Diameters Analysis")
    # -------------------------------- line chart -------------------------------- #
    optionindivtrait = st.selectbox(
        "Color by",
        [
            "family",
            "genus",
            "species",
            "samples_id",
            "parent_id",
            "sample_class",
            "sample_tag",
            "silk_type",
        ],
        key="optiongroupby_diameter",
        index=0,
    )
    with st.expander("Filters", expanded=False):
        diameterfilterfamily = st.multiselect(
            "Family", dfs.family.unique(), dfs.family.unique(), key="diamfilter1"
        )
        diameterfilterspecies = st.multiselect(
            "Species",
            dfs.query("family in @diameterfilterfamily").nomenclature.unique(),
            dfs.query("family in @diameterfilterfamily").nomenclature.unique(),
            key="diamfilter2",
        )
        diameterfiltertag = st.multiselect(
            "Tag", dfs.tag.unique(), dfs.tag.unique(), key="diamfilter4"
        )
        diameterfiltersilktype = st.multiselect(
            "Silk type",
            dft1.silk_type.unique(),
            dft1.silk_type.unique(),
            key="diamfilter5",
        )
        diameterfiltersample = st.multiselect(
            "Sample", dfs.query("family in @diameterfilterfamily").query("sample_class in 'silksample'").id.unique(), dfs.query("family in @diameterfilterfamily").query("sample_class in 'silksample'").id.unique(), key="diamfilter3"
        )
    startdated = st.slider(
        "Show only diameter  for data uploaded after this date",
        min_value=datetime.datetime.fromisocalendar(2020, 1, 1),
        max_value=datetime.datetime.fromisocalendar(2024, 1, 1),
        value=datetime.datetime.fromisocalendar(2022, 1, 1),
    )
    nbinslider = st.slider(
        "Number of histogram bins", min_value=1, max_value=100, value=20
    )

    figtraithistd = px.histogram(
        dft1.query("family in @diameterfilterfamily")
        .query("nomenclature in @diameterfilterspecies")
        .query("samples_id in @diameterfiltersample")
        .query("sample_tag in @diameterfiltertag")
        .query("silk_type in @diameterfiltersilktype")
        .query("uploaddate > @startdated"),
        x="diameter",
        nbins=nbinslider,
        color=optionindivtrait,
    )
    st.plotly_chart(figtraithistd)
    st.dataframe(dft1.query("family in @diameterfilterfamily")
        .query("nomenclature in @diameterfilterspecies")
        .query("samples_id in @diameterfiltersample")
        .query("sample_tag in @diameterfiltertag")
        .query("silk_type in @diameterfiltersilktype")
        .query("uploaddate > @startdated")
        )
    try:
        st.write(f"Diameter statistics grouped by {optionindivtrait}")
        st.dataframe(
            dft1.query("family in @diameterfilterfamily")
            .query("nomenclature in @diameterfilterspecies")
            .query("samples_id in @diameterfiltersample")
            .query("sample_tag in @diameterfiltertag")
            .query("silk_type in @diameterfiltersilktype")
            .query("uploaddate > @startdated")
            .groupby(optionindivtrait)["diameter"]
            .describe(include=[np.number])
            .transpose()
        )
    except Exception as e:
        st.write(e)
# ---------------------------------------------------------------------------- #
#                               individual trait                               #
# ---------------------------------------------------------------------------- #
with tabs[4]:
    optionindivtrait = st.selectbox(
        "Select a trait",
        ["weight", "body_length"],
        key="optionindivtrait",
        index=0,
    )
    st.write(f"## {optionindivtrait} analysis")
    # --------------------------------- histogram -------------------------------- #
    optiongroupby = st.selectbox(
        "Color by",
        ["family", "genus", "species", "samples_id", "sample tag"],
        key="optiongroupby_mass",
        index=0,
    )
    with st.expander("Filters", expanded=False):
        weightfilterfamily = st.multiselect(
            "Family", dfs.family.unique(), dfs.family.unique(), key="weifilter1"
        )
        weightfilterspecies = st.multiselect(
            "Species",
            dfs.nomenclature.unique(),
            dfs.nomenclature.unique(),
            key="weifilter2",
        )
        weightfiltersample = st.multiselect(
            "Sample", dfs.id.unique(), dfs.id.unique(), key="weifilter3"
        )
        weightfiltertag = st.multiselect(
            "Tag", dfs.tag.unique(), dfs.tag.unique(), key="weifilter4"
        )
    startdate = st.slider(
        "Show only weight data uploaded after this date",
        min_value=datetime.datetime.fromisocalendar(2021, 1, 1),
        max_value=datetime.datetime.fromisocalendar(2024, 1, 1),
        value=datetime.datetime.fromisocalendar(2022, 1, 1),
    )
    nbinslider = st.slider(
        "Number of histogram bins",
        min_value=1,
        max_value=1000,
        value=20,
        key="individualbinsslider",
    )
    # minmaxdf = dft2.agg([min, max])
    # mintraitval, maxtraitval = st.slider("Select range", value=[minmaxdf.loc["min",optionindivtrait],minmaxdf.loc["max",optionindivtrait]])

    figtraithist = px.histogram(
        dft2.query("family in @weightfilterfamily")
        .query("nomenclature in @weightfilterspecies")
        .query("samples_id in @weightfiltersample")
        .query("sample_tag in @weightfiltertag")
        .query("uploaddate > @startdate"),
        x=optionindivtrait,
        nbins=nbinslider,
        color=optiongroupby,
        log_x=True,
    ).update_layout(xaxis_title="Body length (mm)")
    st.plotly_chart(figtraithist)

    try:
        st.write(f"{optionindivtrait} statistics grouped by {optiongroupby}")
        st.dataframe(
            dft2.groupby(optiongroupby)[optionindivtrait]
            .describe(include=[np.number])
            .transpose()
        )
    except Exception as e:
        st.write(e)

# ---------------------------------------------------------------------------- #
#                                  experiments                                 #
# ---------------------------------------------------------------------------- #
try:
    with tabs[5]:
        st.write("# Experiments")

        tensileselector = st.multiselect(
            "Experiment",
            dftensile.id.unique(),
            dftensile.id.unique(),
            key="tensileselector",
        )
        dfjson = pd.DataFrame(
            columns=["EngineeringStrain", "EngineeringStress", "LoadOnSpecimen", "Time"]
        )
        id = int(0)
        for measure in dftensile.query("id in @tensileselector").measure:
            currentdf = pd.read_json(measure, orient="split")
            currentdf["id"] = str(id)
            id += 1
            dfjson = pd.concat([dfjson, currentdf])

        tensileplot = px.scatter(
            dfjson, x="EngineeringStrain", y="LoadOnSpecimen", color="id"
        )
        st.plotly_chart(tensileplot)
except:
    ...
# ---------------------------------------------------------------------------- #
#                                chart generator                               #
# ---------------------------------------------------------------------------- #
with tabs[6]:
    st.write("# Choose the dataframe to display")
    st.write(
        "We suggest activating 'wide mode' by pressing the three dots on the top right corner of this screen and selecting Settings"
    )
    selecteddataframe = st.selectbox(
        "Select a dataframe",
        ["Sample", "Silk Trait"],
        key="pygselectdf",
        index=0,
    )
    if selecteddataframe == "Sample":
        pyg_html = pyg.walk(dfs, return_html=True)
    if selecteddataframe == "Silk Trait":
        pyg_html = pyg.walk(dft1, return_html=True)
    # Embed the HTML into the Streamlit app
    components.html(pyg_html, height=1000, scrolling=True)
# ---------------------------------------------------------------------------- #
#                            tensile test converter                            #
# ---------------------------------------------------------------------------- #
with tabs[7]:
    from io import StringIO, BytesIO

    buffer = BytesIO()

    @st.cache_resource
    def convert_df(measures: list[pd.DataFrame]):
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            for index, measure in enumerate(measures):
                measure.to_excel(writer, sheet_name="Sheet_name_" + str(index))

    st.write("# Drop here the files to be converted")
    files = st.file_uploader(label="txt files", accept_multiple_files=True)
    convert = st.button("Convert")
    conv = []
    if convert:
        if len(files) > 0:
            for file in files:
                conv.append(StringIO(file.getvalue().decode("utf-8")))
        [measures, attributes] = getattributesandmeasureformultiplefiles(conv)
        convert_df(measures)
    st.download_button(
        "Download",
        buffer.getvalue(),
        file_name="converted.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


# with tabs[0]:
#     st.experimental_data_editor(
#         dft1,
#         width=None,
#         height=None,
#         use_container_width=False,
#         num_rows="dynamic",
#         on_change=dfs.to_sql("sample", engine, if_exists='replace'),
#     )
