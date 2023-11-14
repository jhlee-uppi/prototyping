
import streamlit as st
from streamlit_extras.stylable_container import stylable_container
from annotated_text import annotated_text
# from streamlit_option_menu import option_menu

import pandas as pd
import geopandas as gpd

import numpy as np
import os
import plotly.express as px
from PIL import Image

from folium.features import DivIcon
from streamlit_folium import st_folium
import folium

st.set_page_config(layout="wide", initial_sidebar_state="collapsed")

# with st.sidebar:
#     selected = option_menu("Main Menu", ["Home", 'Settings'], 
#         icons=['house', 'gear'], menu_icon="cast", default_index=1)
#     selected

col_0_1, col_0_2 = st.columns([0.7,0.3])

with col_0_1:
    st.markdown("# Fiscal Impact Simulator")

with col_0_2:
    image = Image.open('static/EJBlogo_redgray.png')
    st.image(image, output_format = 'PNG', width = 300)

# st.sidebar.markdown("# Fiscal Impact Simulator")
# st.divider()
    
# @st.cache_data
def load_data():
    
    # datasets
    df_DM_NJ_t01 = pd.read_csv('data/DM_NJ_2021ACS_tableIIB1.csv')
    df_DM_NJ_t02 = pd.read_csv('data/DM_NJ_2021ACS_tableIIB2.csv')
    df_Mun_NJ_FIA = pd.read_csv('data/FIA_NJ_110723.csv')

    # municipalities with K-12 school districts
    df_Mun_NJ_FIA = df_Mun_NJ_FIA.loc[~df_Mun_NJ_FIA.LEAID.isna()]
    df_Mun_NJ_FIA = df_Mun_NJ_FIA.loc[~df_Mun_NJ_FIA.LEAID.isna()]

    # calculations
    df_Mun_NJ_FIA_ = df_Mun_NJ_FIA[['County', 'Municipality',
                                    'levy_mun_rShare_perCap','levy_school_perPupil',
                                    'taxRate_sum_mun_sch']]
    df_Mun_NJ_FIA_ = df_Mun_NJ_FIA_.rename({'levy_mun_rShare_perCap':'MunLevy_PC',
                                            'levy_school_perPupil':'SchLevy_PP',
                                            'taxRate_sum_mun_sch':'SumRate_Mun_Sch'}, axis=1)

    # parameters for selector
    df_Mun_NJ_FIA_MunList = df_Mun_NJ_FIA_[['County','Municipality']]
    df_Mun_NJ_FIA_MunList['MunLabel'] = df_Mun_NJ_FIA_MunList.apply(lambda x: '{} ({})'.format(x.Municipality,x.County),axis=1)

    return df_DM_NJ_t01, df_DM_NJ_t02, df_Mun_NJ_FIA, df_Mun_NJ_FIA_, df_Mun_NJ_FIA_MunList
    
df_DM_NJ_t01, df_DM_NJ_t02, df_Mun_NJ_FIA, df_Mun_NJ_FIA_, df_Mun_NJ_FIA_MunList = load_data()

tab1, tab2, tab3, tab9 = st.tabs(["Municipality", "Simulator", "Dashboard","About"])

with tab1:
        
    col_mun_1, col_mun_2 = st.columns([0.8,0.2])
    
    with col_mun_2:
        select_State = st.selectbox('State',
                                    ['New Jersey'])
        select_County = st.selectbox('County',
                                  df_Mun_NJ_FIA_MunList.County.drop_duplicates())
    
        select_Mun = st.selectbox('Municipality',
                                  df_Mun_NJ_FIA_MunList.loc[
                                  df_Mun_NJ_FIA_MunList.County == select_County,
                                  'Municipality'].drop_duplicates())
    @st.cache_data
    def load_geojson():
        # map
        geo_NJ = gpd.read_file('data/Municipal_Boundaries_of_NJ.geojson.zip')
        geo_NJ['County'] = geo_NJ['COUNTY'].str.title()
        geo_NJ['Municipality'] = geo_NJ['MUN_LABEL']
    
        cond_city2 = ~geo_NJ.Municipality.isin(df_Mun_NJ_FIA_MunList.Municipality) & geo_NJ.Municipality.str.contains('City')
        geo_NJ.loc[cond_city2,'Municipality'] = geo_NJ['Municipality'].str.replace('City','City City')
    
        return geo_NJ
    geo_NJ = load_geojson()
    
    with col_mun_1:
        tb_target = df_Mun_NJ_FIA_MunList[
            (df_Mun_NJ_FIA_MunList.Municipality == select_Mun) &
            (df_Mun_NJ_FIA_MunList.County == select_County) ]
        
        geo_target = geo_NJ.merge(tb_target)
        geo_target['lon'] = geo_target.representative_point().x
        geo_target['lat'] = geo_target.representative_point().y
        
        m = folium.Map(location=[ geo_target['lat'].iloc[0], geo_target['lon'].iloc[0] ],
                       min_zoom = 11,max_zoom=13,zoom_start=12, zoom_control = False,
                       tiles="CartoDB positron")
        sim_geo = gpd.GeoSeries(geo_target["geometry"]).simplify(tolerance=0.0001).to_crs(4326)
        geo_j = sim_geo.to_json()
        geo_j = folium.GeoJson(data=geo_j, 
                               style_function=lambda x: {"fillOpacity": .5, 'fillColor':'#CC0033', 
                                                         'color':'#CC0033'})
        folium.map.Marker(
              [ geo_target['lat'].iloc[0], geo_target['lon'].iloc[0] ],
              icon=DivIcon(
                  icon_size=(400,50),
                  icon_anchor=(200,25),
                  html=f'<div style="font-size:14px; color:black;' +
                       f'font-weight:bold;text-align:center;vertical-align: middle;">' +
                       f'{geo_target["MunLabel"].iloc[0]}</div>')).add_to(m)
        
        geo_j.add_to(m)
        mun_map = st_folium(m, height = 400, use_container_width = True)

        import leafmap.foliumap as leafmap

        m2 = leafmap.Map(
            search_control = False,
            layers_control=False,
                         draw_control=False,
                         measure_control=False,
                         fullscreen_control=False,
                         attribution_control=False)
        m2.add_basemap('CartoDB.PositronNoLabels')
        m2.add_gdf(geo_target)
        html=f'<div style="font-size:14px; color:black;'
        html=html+f'font-weight:bold;text-align:center;vertical-align: middle;">'
        html=html+f'{geo_target["MunLabel"].iloc[0]}</div>'
        m2.add_labels(
            geo_target,
            'MunLabel',
            font_size="14pt",
            font_color="black",
            font_family="arial",
            font_weight="bold",
            (html = html)
        )
        
        m2.to_streamlit(height=400, )

with tab2:
    with stylable_container(
        key="mun_nav",
        css_styles="""
            {
                border: 1px solid rgba(49, 51, 63, 0.2);
                border-radius: 0.5rem;
                padding: calc(1em - 5px)
            }
            """,
    ):
        annotated_text(
            "**Selected Municipality**", " ", (select_State, "state", "#d6d7da"), " ", (select_County, "county", "#d6d7da")," ",(select_Mun, "municipality", "#d6d7da")
        )      
    
    param_HousingType = 'Single-Family Detached  (Own/Rent), 4-5 BR'
    param_ValueType = 'All Values'
    
    # breakeven analysis
    df_DM_NJ_t01_ = df_DM_NJ_t01.loc[(df_DM_NJ_t01.HousingType == param_HousingType) & (df_DM_NJ_t01.ValueType == param_ValueType),['PERSONS']]
    df_DM_NJ_t01_ = df_DM_NJ_t01_.iloc[0][0]
    df_DM_NJ_t02_ = df_DM_NJ_t02.loc[(df_DM_NJ_t02.HousingType == param_HousingType) & (df_DM_NJ_t02.ValueType == param_ValueType),['TotalSAC']]
    df_DM_NJ_t02_ = df_DM_NJ_t02_.iloc[0][0]
    
    df_Mun_NJ_FIA_['MunCost_unit'] = df_Mun_NJ_FIA_['MunLevy_PC'] * df_DM_NJ_t01_
    df_Mun_NJ_FIA_['SchCost_unit'] = df_Mun_NJ_FIA_['SchLevy_PP'] * df_DM_NJ_t02_
    df_Mun_NJ_FIA_['TotCost_unit'] = df_Mun_NJ_FIA_['MunCost_unit']+df_Mun_NJ_FIA_['SchCost_unit']
    df_Mun_NJ_FIA_['Breakeven_Mvalue'] = df_Mun_NJ_FIA_['TotCost_unit'] / (df_Mun_NJ_FIA_['SumRate_Mun_Sch']/100)
    
    # Breakeven Analysis Table
    de_breakeven_in = pd.DataFrame(
        {
            "HousingType": [df_DM_NJ_t01.HousingType.drop_duplicates().tolist()[0]],
            "num_units": [1],
            "buyoutMValue":[0]
        }
    )
    
    
    de_breakeven_out = pd.DataFrame(
        {
            "BE_MValue": []
        }
    )

    col_BE_1, col_BE_2 = st.columns([0.8, 0.2])
    
    with col_BE_1:
        st.markdown("### Input")
        de_breakeven_cal = st.data_editor(
            de_breakeven_in, #.style.format({"buyoutMValue": "$ {:,.0f}"}), # this part is problematic; makes the simulator uneditable
            use_container_width = True,
            column_config={
                "HousingType": st.column_config.SelectboxColumn(
                    "Housing Type",
                    help="The category of housing units",
                    width='medium',
                    options=df_DM_NJ_t01.HousingType.drop_duplicates().tolist(),
                    required=True,
                ),
                "num_units": st.column_config.NumberColumn(
                    "# units",
                    help="The number of housing units",
                    min_value=0,
                    max_value=100,
                    step=1,
                    format="%d",
                ),
                "buyoutMValue": st.column_config.NumberColumn(
                    "Avg Value",
                    help="Average market value of buy-out properties",
                    min_value=0,
                    max_value=None,
                    step=1,
                    # format="%d",
                )
            },
            hide_index=True,
            num_rows = 'dynamic'
        )
    
    with col_BE_2:
        st.markdown("### Output")
        de_breakeven_out_ = pd.DataFrame(de_breakeven_cal)
        de_breakeven_out_['ValueType'] = 'All Values'
        de_breakeven_out_ = de_breakeven_out_.merge(df_DM_NJ_t01[['HousingType', 'ValueType','PERSONS']], how = 'left')
        de_breakeven_out_ = de_breakeven_out_.merge(df_DM_NJ_t02[['HousingType', 'ValueType','TotalSAC']], how = 'left')
    
        select_mun_county = df_Mun_NJ_FIA_MunList[
        (df_Mun_NJ_FIA_MunList.Municipality == select_Mun)&
        (df_Mun_NJ_FIA_MunList.County == select_County)][['County','Municipality']]
        select_mun_be = df_Mun_NJ_FIA_[
        ['County','Municipality','MunLevy_PC','SchLevy_PP',
         'SumRate_Mun_Sch']].merge(select_mun_county)
    
        de_breakeven_out_['MunCost_unit'] = de_breakeven_out_['PERSONS']*select_mun_be['MunLevy_PC'].iloc[0]
        de_breakeven_out_['SchCost_unit'] = de_breakeven_out_['TotalSAC']*select_mun_be['SchLevy_PP'].iloc[0]
    
        de_breakeven_out_['TotCost_unit'] = de_breakeven_out_['MunCost_unit'] + de_breakeven_out_['SchCost_unit']
        de_breakeven_out_['BreakevenMValue'] = de_breakeven_out_['TotCost_unit'] / (select_mun_be['SumRate_Mun_Sch'].iloc[0]/100)
        de_breakeven_out_['FiscalBalance_unit'] = - (de_breakeven_out_['BreakevenMValue'] - de_breakeven_out_['buyoutMValue'])
        de_breakeven_out_['FiscalBalance_total'] = de_breakeven_out_['FiscalBalance_unit'] * de_breakeven_out_['num_units']
    
        # de_breakeven_out_
        
        st.data_editor(
            de_breakeven_out_[['FiscalBalance_total']
            ].style.format({"FiscalBalance_total": "$ {:,.0f}"}),
            use_container_width = True,
                       column_config={
                       "FiscalBalance_total": st.column_config.NumberColumn(
                    "Fiscal Balance",
                    help="Fiscal surplus or deficit",
                    min_value=None,
                    max_value=None,
                    step=1,
                           disabled=True,
                )
                       },
                      hide_index=True)

with tab3:
    with stylable_container(
        key="mun_nav",
        css_styles="""
            {
                border: 1px solid rgba(49, 51, 63, 0.2);
                border-radius: 0.5rem;
                padding: calc(1em - 5px)
            }
            """,
    ):
        annotated_text(
            "**Selected Municipality**", " ", (select_State, "state", "#d6d7da"), " ", (select_County, "county", "#d6d7da")," ",(select_Mun, "municipality", "#d6d7da")
        )

    col_Dash_1, col_Dash_2 = st.columns(2)

    with col_Dash_1:
        fig1_data = de_breakeven_out_[['HousingType','MunCost_unit','SchCost_unit']
        ].melt(id_vars = 'HousingType', value_vars = ['MunCost_unit','SchCost_unit'])
        
        fig1 = px.histogram(fig1_data, 
                            x="HousingType", y="value",
                            color='variable', barmode='group',
                            height=400)
        
        st.plotly_chart(fig1, use_container_width = True)
        
    with col_Dash_2:
        fig2_data = de_breakeven_out_[['HousingType','BreakevenMValue','buyoutMValue','FiscalBalance_unit']
        ].melt(id_vars = 'HousingType', value_vars = ['BreakevenMValue','buyoutMValue','FiscalBalance_unit'])
        
        fig2 = px.histogram(fig2_data, 
                            x="HousingType", y="value",
                            color='variable', barmode='group',
                            height=400)
        
        st.plotly_chart(fig2, use_container_width = True)

with tab9:
    st.markdown('''
    - This simulator involves New Jersey municipalities with their own K–12 school districts: `212`/`565` (`37.5%` coverage).
        - E.g., `Hoboken City` - `Hoboken Public School District`
    - `11/07/2023` version
    ''')

# st.divider()
