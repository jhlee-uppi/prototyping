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
import leafmap.foliumap as leafmap

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
    df_DM_NJ_t01 = pd.read_csv('data/DM_NJ_2021ACS_tableIIB1_.csv')
    df_DM_NJ_t02 = pd.read_csv('data/DM_NJ_2021ACS_tableIIB2_.csv')
    df_Mun_NJ_FIA = pd.read_csv('data/FIA_NJ_110723.csv')
    df_Mun_NJ_Buyout = pd.read_csv('data/111823_buyout_values.csv')

    # municipalities with K-12 school districts
    df_Mun_NJ_FIA = df_Mun_NJ_FIA.loc[~df_Mun_NJ_FIA.LEAID.isna()]
    df_Mun_NJ_FIA = df_Mun_NJ_FIA.loc[~df_Mun_NJ_FIA.LEAID.isna()]

    # buyout avg price
    df_Mun_NJ_Buyout = df_Mun_NJ_Buyout.loc[(df_Mun_NJ_Buyout.flag != 'E') & ~df_Mun_NJ_Buyout.Municipality.isna()]
    df_Mun_NJ_Buyout['AVERAGE_VALUE_BUYOUT_PROPERTY'].str.replace('[^0-9]+','').astype(str)
    df_Mun_NJ_Buyout['buyout_avg_value'] = df_Mun_NJ_Buyout['AVERAGE_VALUE_BUYOUT_PROPERTY'].str.replace('[^0-9]+','',regex = True)
    
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
    df_Mun_NJ_Buyout_city = df_Mun_NJ_Buyout.loc[df_Mun_NJ_Buyout.Municipality.str.contains('City')]
    df_Mun_NJ_Buyout_city['Municipality'] = df_Mun_NJ_Buyout_city.Municipality.str.replace('City','City City', regex = False)
    df_Mun_NJ_Buyout_mod = pd.concat([df_Mun_NJ_Buyout,df_Mun_NJ_Buyout_city], axis = 0).reset_index(drop = True)

    return df_DM_NJ_t01, df_DM_NJ_t02, df_Mun_NJ_FIA, df_Mun_NJ_FIA_, df_Mun_NJ_FIA_MunList, df_Mun_NJ_Buyout_mod
    
df_DM_NJ_t01, df_DM_NJ_t02, df_Mun_NJ_FIA, df_Mun_NJ_FIA_, df_Mun_NJ_FIA_MunList, df_Mun_NJ_Buyout_mod = load_data()

df_DM_NJ_t01.HousingType = df_DM_NJ_t01.HousingType.str.replace(' +\\(.*\\),*',',',regex = True)
df_DM_NJ_t02.HousingType = df_DM_NJ_t02.HousingType.str.replace(' +\\(.*\\),*',',',regex = True)

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
        geo_target['MunLabel'] = geo_target['MunLabel'].str.replace('City City','City')
        
        # m = folium.Map(location=[ geo_target['lat'].iloc[0], geo_target['lon'].iloc[0] ],
        #                min_zoom = 11,max_zoom=13,zoom_start=12, zoom_control = False,
        #                tiles="CartoDB positron")
        sim_geo = gpd.GeoSeries(geo_target["geometry"]).simplify(tolerance=0.0001).to_crs(4326)
        geo_j = sim_geo.to_json()
        geo_j = folium.GeoJson(data=geo_j, 
                               style_function=lambda x: {"fillOpacity": .5, 'fillColor':'#CC0033', 
                                                         'color':'#CC0033'})
        # folium.map.Marker(
        #       [ geo_target['lat'].iloc[0], geo_target['lon'].iloc[0] ],
        #       icon=DivIcon(
        #           icon_size=(400,50),
        #           icon_anchor=(200,25),
        #           html=f'<div style="font-size:14px; color:black;' +
        #                f'font-weight:bold;text-align:center;vertical-align: middle;">' +
        #                f'{geo_target["MunLabel"].iloc[0]}</div>')).add_to(m)
        
        # geo_j.add_to(m)
        # mun_map = st_folium(m, height = 400, use_container_width = True)

        

        m2 = leafmap.Map(
            search_control = False,
            layers_control=False,
                         draw_control=False,
                         measure_control=False,
                         fullscreen_control=False,
                         attribution_control=False)
        m2.add_basemap('CartoDB.PositronNoLabels')
        
        style = {
                # "stroke": True,
                "color": "#CC0033",
                "weight": 3,
                "opacity": 1,
                "fill": True,
                "fillColor": "#CC0033",
                "fillOpacity": 0.5,
                # "dashArray": "9"
                # "clickable": True,
            }
        m2.add_gdf(geo_target, style = style)
        m2.add_labels(
            geo_target,
            'MunLabel',
            font_size="11pt",
            font_color="black",
            font_family="arial",
            font_weight="bold"
        )
        
        m2.to_streamlit(height=400, )

# select_list_housingType = []

def _select_list():
    try:
        return select_list_housingType
    except:
        return df_DM_NJ_t01.HousingType.drop_duplicates().tolist()
        
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
            "**Selected Municipality**", " ", 
            (select_State, "state", "#d6d7da"), " ", 
            (select_County, "county", "#d6d7da")," ",
            (select_Mun, "municipality", "#d6d7da")
        )      
    
    param_HousingType = 'Single-Family Detached, 4-5 BR'
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
    # df_Mun_NJ_FIA_ = df_Mun_NJ_FIA_.merge(df_Mun_NJ_Buyout, how = 'left')
    
    # Breakeven Analysis Table
    de_breakeven_in = pd.DataFrame(
        {
            "HousingType": df_DM_NJ_t01.HousingType.drop_duplicates().iloc[[0,1,2,3]].tolist(),
            "num_units": [1,1,1,1],
            "buyoutMValue":[0,0,0,0]
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
                "HousingType": st.column_config.TextColumn(
                    "Housing Type",
                    help="The category of housing units",
                    width='medium',
                    disabled = True
                    # options=_select_list(),#df_DM_NJ_t01[~df_DM_NJ_t01.HousingType.isin(select_list_housingType)].HousingType.drop_duplicates().tolist(),
                    # required=True,
                ),
                # "HousingType": st.column_config.SelectboxColumn(
                #     "Housing Type",
                #     help="The category of housing units",
                #     width='medium',
                #     options=_select_list(),#df_DM_NJ_t01[~df_DM_NJ_t01.HousingType.isin(select_list_housingType)].HousingType.drop_duplicates().tolist(),
                #     required=True,
                # )
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
            num_rows = 'fixed' # dynamic
        )

        select_list_housingType = df_DM_NJ_t01[~df_DM_NJ_t01.HousingType.isin(de_breakeven_cal.HousingType)]
        select_list_housingType = select_list_housingType.HousingType.drop_duplicates().tolist()

        # select_list_housingType = select_list_housingType[select_list_housingType.isin(de_breakeven_cal.HousingType)]
        # df_DM_NJ_t01[~df_DM_NJ_t01.HousingType.isin(select_list_housingType)].HousingType.drop_duplicates().tolist()
        # st.dataframe(_select_list())

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

    # st.markdown('''

    # ### :red[Streamlit] :orange[can] :green[write] :blue[text] :violet[in]
    # #### :gray[pretty] :rainbow[colors].
    # ''')

    # for i in range(5):
    
    col_Dash_1, col_Dash_2 = st.columns(2)

    def _summary_text_return(list_HousingType, data):
        _summary_text = []
        for i in list_HousingType:
            _summary_data = data.loc[data.HousingType == i]
            _summary_data_type = _summary_data.HousingType.iloc[0]
            _summary_data_bv = _summary_data.loc[_summary_data.variable == 'BreakevenMValue','value'].iloc[0]
            _summary_data_bv = int(_summary_data_bv)
            _summary_data_mv = _summary_data.loc[_summary_data.variable == 'buyoutMValue','value'].iloc[0]
            _summary_data_mv = int(_summary_data_mv)
            _summary_data_fb = _summary_data.loc[_summary_data.variable == 'FiscalBalance_unit','value'].iloc[0]
            _summary_data_fb = int(_summary_data_fb)
            _summary_data_fb_color = 'red' if _summary_data_fb<0 else 'blue'
            str_print = f'- **{_summary_data_type}**\n    - **Breakeven Value**: $ {_summary_data_bv:,}\n'
            str_print = str_print + f'    - **Market Value**: $ {_summary_data_mv:,}\n'
            str_print = str_print + f'    - **Fiscal Balance**: **:{_summary_data_fb_color}[$ {_summary_data_fb:,}]**\n'
            _summary_text.append(str_print)
            _summary_text = ''.join(_summary_text)
        return _summary_text
        
    with col_Dash_1:
        fig1_data = de_breakeven_out_[['HousingType','MunCost_unit','SchCost_unit']
        ].melt(id_vars = 'HousingType', value_vars = ['MunCost_unit','SchCost_unit'])

        fig1_data['HousingType_label'] = fig1_data.HousingType.str.replace(
                'Single-Family','SF'
            ).str.replace(
                'Attached','A'
            ).str.replace(
                'Detached','D'
            ).str.replace('SF ','SF')
            
            fig1_data['var_label'] = fig1_data.variable.str.replace(
                'MunCost_','Municipal'
            ).str.replace(
                'SchCost_','School'
            ).str.replace(
                'unit',''
            )

        _summary_text = []
        for i in fig1_data.HousingType.drop_duplicates():
            _summary_data = fig1_data.loc[fig1_data.HousingType == i]
            _summary_data_type = _summary_data.HousingType.iloc[0]
            _summary_data_mc = _summary_data.loc[_summary_data.variable == 'MunCost_unit','value'].iloc[0]
            _summary_data_mc = int(_summary_data_mc)
            _summary_data_sc = _summary_data.loc[_summary_data.variable == 'SchCost_unit','value'].iloc[0]
            _summary_data_sc = int(_summary_data_sc)
            str_print = f'- **{_summary_data_type}**\n    - **Municipal Cost**: $ {_summary_data_mc:,}\n    - **School Cost**: $ {_summary_data_sc:,}\n'
            _summary_text.append(str_print)
        _summary_text = ''.join(_summary_text)
        st.markdown('##### **Municipal and School Cost per Unit**')
        
        fig1 = px.bar(fig1_data, x="value", y="HousingType_label", orientation='h', color = 'var_label')
        fig1.update_layout(
            title=None,
            xaxis_title="$",
            yaxis_title=None,
            legend_title='Cost per Unit')
        
        st.plotly_chart(fig1, use_container_width = True)

        st.markdown(_summary_text)
    
    with col_Dash_2:
        fig2_data = de_breakeven_out_[['HousingType','BreakevenMValue','buyoutMValue','FiscalBalance_unit']
        ].melt(id_vars = 'HousingType', 
               value_vars = ['BreakevenMValue','buyoutMValue','FiscalBalance_unit']
              )

        st.markdown('##### **Fiscal Surplus or Deficit per Unit**', unsafe_allow_html = True)
        fig2 = px.histogram(fig2_data, 
                            x="HousingType", y="value",
                            color='variable', barmode='group',
                            height=400)
        
        st.plotly_chart(fig2, use_container_width = True)

        df_Mun_NJ_Buyout_select = df_Mun_NJ_Buyout_mod.loc[
        (df_Mun_NJ_Buyout_mod.County == select_County) & 
        (df_Mun_NJ_Buyout_mod.Municipality == select_Mun)]

        _buyout_Mvalue = 'N/A'
        str_print = f'- **Average Market Value of Buyout Properties**: $ N/A\n'
        
        if len(df_Mun_NJ_Buyout_select)>0:
            _buyout_Mvalue = df_Mun_NJ_Buyout_select.buyout_avg_value.iloc[0]
            _buyout_Mvalue = int(_buyout_Mvalue)
            
            str_print = f'- **Average Market Value of Buyout Properties**: $ {_buyout_Mvalue:,}\n'

        _summary_text = []
        _summary_text.append(str_print)
        
        for i in fig1_data.HousingType.drop_duplicates():
            _summary_data = fig2_data.loc[fig2_data.HousingType == i]
            _summary_data_type = _summary_data.HousingType.iloc[0]
            _summary_data_bv = _summary_data.loc[_summary_data.variable == 'BreakevenMValue','value'].iloc[0]
            _summary_data_bv = int(_summary_data_bv)
            _summary_data_mv = _summary_data.loc[_summary_data.variable == 'buyoutMValue','value'].iloc[0]
            _summary_data_mv = int(_summary_data_mv)
            _summary_data_fb = _summary_data.loc[_summary_data.variable == 'FiscalBalance_unit','value'].iloc[0]
            _summary_data_fb = int(_summary_data_fb)
            _summary_data_fb_color = 'red' if _summary_data_fb<0 else 'blue'
            str_print = f'- **{_summary_data_type}**\n    - **Breakeven Value**: $ {_summary_data_bv:,}\n'
            str_print = str_print + f'    - **Market Value**: $ {_summary_data_mv:,}\n'
            str_print = str_print + f'    - **Fiscal Balance**: **:{_summary_data_fb_color}[$ {_summary_data_fb:,}]**\n'
            _summary_text.append(str_print)
        _summary_text = ''.join(_summary_text)
        st.markdown(_summary_text)

with tab9:
    st.markdown('''
    - This simulator includes New Jersey municipalities with their own K–12 school districts: `212`/`565` (`37.5%` coverage).
        - E.g., `Hoboken City` - `Hoboken Public School District`
    - `11/27/2023` version
    ''')
