
import streamlit as st
import pandas as pd
import numpy as np
import os

import plotly.express as px

st.markdown("# Fiscal Impact Simulator")
st.sidebar.markdown("# Fiscal Impact Simulator")
st.markdown("07/20/2023 version")
st.divider()

df_basic_info_index = ['Population', '# workers',
                       '# homes in flood plain', '# business in flood plain', 
                       '# of buildings demolished', 'Cost per Demolition ($)',
                       'Total Assessed Value ($)','Total Parcels',
                       'Median Household Assessed Value ($)', 'Median Commercial Assessed Value ($)',
                       'Owner-Occupied Housing (%)', 'Jobs per Commercial Unit']

df_basic_info = pd.DataFrame({'value':[5005, 900, 
                                       1200, 35, 
                                       0, 2500,
                                       598843600,2367,
                                       219000,580000,
                                       58.6,2.5]},
                             index = df_basic_info_index)

st.markdown("## Inputs")
st.sidebar.markdown("## Inputs")

st.markdown("### Basic Information")
st.sidebar.markdown("### Basic Information")

col_1_1, col_1_2 = st.columns(2)

with col_1_1:
    numRows = len(df_basic_info_index)
    df_basic_info_colconfig = {'_index': st.column_config.Column(disabled=True)}
    edit_df_basic_info = st.data_editor(df_basic_info, 
                                        column_config=df_basic_info_colconfig,
                                        height = ((numRows + 1) * 35 + 3) )

# slider

with col_1_2:
    percent_value_change = st.slider('Assessed Property Value Change (%)', 
                                  -100, 100, -40, step = 1, label_visibility='visible',
                                  format = '%i%%')
    
    percent_pop_change = st.slider('Population Change (%)', 
                                  -100, 100, -50, step = 1, label_visibility='visible',
                                  format = '%i%%')
    
    percent_sticky_expenditure = st.slider('"Sticky" Expenditures (%)', 
                                           0, 100, 50, step = 1, label_visibility='visible',
                                           format = '%i%%')
    percent_sticky_expenditure_inv = 100-percent_sticky_expenditure
    
    percent_tax_rate_municipal = st.slider('Municipal Purpose Tax Rate (%)', 
                                       0.0, 10.0, 1.031, step = 0.001, label_visibility='visible',
                                       format = '%.3f%%')
    percent_tax_rate_schooldist = st.slider('School District Tax Rate (%)', 
                                       0.0, 10.0, 1.185, step = 0.001, label_visibility='visible',
                                       format = '%.3f%%')

    dt_simulations_aggr = pd.DataFrame()

sim_save_div_0 = st.empty()
sim_result_title = st.empty()
# sim_result_title_sidebar = st.empty()
sim_result_summary = st.empty()
sim_save_button = st.empty()
sim_saved_sims = st.empty()
sim_save_div_1 = st.empty()
    
st.markdown("### Other Parameters")
st.sidebar.markdown("### Other Parameters")

total_cost_change = None
total_rev_change = None

tab_2_1, tab_2_2, tab_2_3, tab_2_4 = st.tabs(["Population Change", "Residential Share", "Change in Expenditures", "Change in Revenues"])

with tab_2_1: # Population Change
    
    st.markdown("#### Input Table")
    
    df_pop_change_input_index =['# of housing units in bedroom class',
                                 'Person per unit: Owner-Occupied Units',
                                 'Person per unit: Renter-Occupied Units']
    
    df_pop_change_input = pd.DataFrame({'0-1 br': [1038,2.139,1.655], 
                                        '2 br':[1085, 1.933,2.453], 
                                        '3 br':[654,2.851,3.466],
                                        '4br':[212,3.767,4.572]},
                                       index = df_pop_change_input_index)
    
    df_pop_change_input_colconfig = {'_index': st.column_config.Column(disabled=True)}
    edit_df_pop_change_input = st.data_editor(df_pop_change_input, column_config = df_pop_change_input_colconfig)

    total_housing = edit_df_pop_change_input.loc['# of housing units in bedroom class',:].sum()
    fraction_housing = edit_df_pop_change_input.loc['# of housing units in bedroom class',:]/total_housing
    loss_housing = fraction_housing * edit_df_basic_info.loc['# homes in flood plain','value'] * percent_pop_change/100
    
    loss_housing_owner = loss_housing * edit_df_basic_info.loc['Owner-Occupied Housing (%)','value'] / 100
    change_pop_housing_owner = loss_housing_owner * edit_df_pop_change_input.loc['Person per unit: Owner-Occupied Units']
    
    loss_housing_renter = loss_housing * (1-(edit_df_basic_info.loc['Owner-Occupied Housing (%)','value'] / 100))
    change_pop_housing_renter = loss_housing_renter * edit_df_pop_change_input.loc['Person per unit: Renter-Occupied Units']
    
    total_change_pop = change_pop_housing_owner.sum() + change_pop_housing_renter.sum()
    total_change_job = edit_df_basic_info.loc['# business in flood plain','value'] * percent_pop_change/100
    total_change_job = total_change_job * edit_df_basic_info.loc['Jobs per Commercial Unit','value']
    
    result_PopChange = ['Total Change in Residents','Total Change in Number of Workers']
    result_PopChange = pd.DataFrame({'value':[total_change_pop, total_change_job]},
                                    index = result_PopChange)
    
    st.markdown("#### Output Table")
    st.dataframe(result_PopChange,
                 column_config={"value": st.column_config.NumberColumn(label = "", format="%d")})
    
with tab_2_2: # Residential Share
    
    st.markdown("#### Input Table")
    
    # col_2_2_1, col_2_2_2 = st.columns(2)
    
    df_assessed_value = ['Total Assessed Value ($)','Residential Assessed Value ($)']
    df_assessed_value = pd.DataFrame({'value':[
        edit_df_basic_info.loc['Total Assessed Value ($)','value'],
        edit_df_basic_info.loc['Total Assessed Value ($)','value']
    ]},
                                     index = df_assessed_value)

    df_parcel = ['Total Parcels','Residential Parcels']
    df_parcel = pd.DataFrame({'value':[
        edit_df_basic_info.loc['Total Parcels','value'],
        edit_df_basic_info.loc['Total Parcels','value']
    ]},
                                     index = df_parcel)
    
    df_ResShare_input_ccfg = {col_i: st.column_config.Column(disabled=True) for col_i in ['_index','Total']}
    df_ResShare_input = ['Assessed Value ($)', '# Parcels']
    df_ResShare_input = pd.DataFrame({'Total': [edit_df_basic_info.loc['Total Assessed Value ($)','value'],
                                                edit_df_basic_info.loc['Total Parcels','value']], 
                                      'Residential':[edit_df_basic_info.loc['Total Assessed Value ($)','value'],
                                                     edit_df_basic_info.loc['Total Parcels','value']]},
                                     index= df_ResShare_input)
    
    edit_df_ResShare_input = st.data_editor(df_ResShare_input, column_config = df_ResShare_input_ccfg)
    
    
    st.markdown("#### Output Table")
    
    fraction_residential_value = edit_df_ResShare_input.loc['Assessed Value ($)','Residential'] / edit_df_ResShare_input.loc['Assessed Value ($)','Total']
    fraction_residential_parcel = edit_df_ResShare_input.loc['# Parcels','Residential'] / edit_df_ResShare_input.loc['# Parcels','Total']
    
    result_ResShare = ['Residential Value Percentage (%)', 'Residential Parcels Percentage (%)', 'Share of Non-Residential Costs and Revenues (%)']
    result_ResShare = pd.DataFrame({'value':[fraction_residential_value*100, 
                                             fraction_residential_parcel*100, 
                                             np.mean([fraction_residential_value, fraction_residential_parcel])*100]
                                   }, index = result_ResShare)
    st.dataframe(result_ResShare,
                 column_config={"value": st.column_config.NumberColumn(label = "", format="%.1f%%")})

with tab_2_3:
    
    import_exp = st.file_uploader("upload expenditure table", type={"csv", "txt"})
    
    if import_exp is not None:
        import_exp_df = pd.read_csv(import_exp)
        
        # try:
        import_exp_df = import_exp_df[['Expenditure','Total','Residential_Only']]
        import_exp_df['Residential_Only'] = import_exp_df['Residential_Only'].fillna(0)

        import_exp_df['Residential'] = import_exp_df.apply(lambda x: x.Total * result_ResShare.loc['Share of Non-Residential Costs and Revenues (%)','value'] / 100,axis=1)
        import_exp_df.loc[import_exp_df.Residential_Only==1,'Residential'] = import_exp_df.loc[import_exp_df.Residential_Only==1,'Total']
        import_exp_df['Non-Residential'] = import_exp_df['Total'] - import_exp_df['Residential']
        import_exp_df = import_exp_df.drop(['Residential_Only'], axis=1)

        st.markdown("#### Input Table")
        st.dataframe(import_exp_df,
                     column_config={col_i: st.column_config.NumberColumn(format = '%i') for col_i in ['Total','Residential','Non-Residential']})

        st.markdown("#### Output Table")

        residential_percap_exp = import_exp_df['Residential'].sum() / edit_df_basic_info.loc['Population','value']
        residential_cost_change = residential_percap_exp * total_change_pop * percent_sticky_expenditure_inv/100
        nonresidential_percap_exp = import_exp_df['Non-Residential'].sum() / edit_df_basic_info.loc['# workers','value']
        nonresidential_cost_change = nonresidential_percap_exp * total_change_job  * percent_sticky_expenditure_inv/100
        demolition_cost = edit_df_basic_info.loc['# of buildings demolished','value'] * edit_df_basic_info.loc['Cost per Demolition ($)','value']
        total_cost_change = residential_cost_change + nonresidential_cost_change + demolition_cost

        result_exp = ['Per-Capita Costs','Change in Residents','Change in residential costs',
                      'Per-Worker Costs','Change in Workers','Change in non-residential costs',
                      '# of Buildings Demolished','Cost per Demolition','Total Demolition Cost',
                      'Change in Total Expenditures']
        result_exp = pd.DataFrame({'value':[residential_percap_exp, total_change_pop, residential_cost_change, 
                                           nonresidential_percap_exp, total_change_job, nonresidential_cost_change,
                                           edit_df_basic_info.loc['# of buildings demolished','value'], 
                                           edit_df_basic_info.loc['Cost per Demolition ($)','value'],
                                           demolition_cost,
                                           total_cost_change],
                                   'sticky':[False,False,True,False,False,True,False,False,False,True]}, 
                                  index=result_exp)

        st.dataframe(result_exp,
                     column_config={col_i: st.column_config.NumberColumn(format = '%i') for col_i in ['value'] })
        st.markdown('✅ "sticky" expenditure applied.')
            
        # except: 
        #     st.text('data format error.')

with tab_2_4:
    
    import_rev = st.file_uploader("upload revenue table", type={"csv", "txt"})

    if import_rev is not None:
        import_rev_df = pd.read_csv(import_rev)
        
        # try:
        import_rev_df = import_rev_df[['Revenue','Total','Residential_Only']]
        import_rev_df['Residential_Only'] = import_rev_df['Residential_Only'].fillna(0)

        import_rev_df['Residential'] = import_rev_df.apply(lambda x: x.Total * result_ResShare.loc['Share of Non-Residential Costs and Revenues (%)','value'] / 100,axis=1)
        import_rev_df.loc[import_rev_df.Residential_Only==1,'Residential'] = import_rev_df.loc[import_rev_df.Residential_Only==1,'Total']
        import_rev_df['Non-Residential'] = import_rev_df['Total'] - import_rev_df['Residential']
        import_rev_df = import_rev_df.drop(['Residential_Only'], axis=1)

        st.markdown("#### Input Table")
        st.dataframe(import_rev_df,
                     column_config={col_i: st.column_config.NumberColumn(format = '%i') for col_i in ['Total','Residential','Non-Residential']})

        st.markdown("#### Output Table")

        residential_percap_rev = import_rev_df['Residential'].sum() / edit_df_basic_info.loc['Population','value']
        residential_rev_change = residential_percap_rev * total_change_pop 
        nonresidential_percap_rev = import_rev_df['Non-Residential'].sum() / edit_df_basic_info.loc['# workers','value']
        nonresidential_rev_change = nonresidential_percap_rev * total_change_job
        general_rev_change = residential_rev_change + nonresidential_rev_change
        assessed_val_change = edit_df_basic_info.loc['# homes in flood plain','value'] * edit_df_basic_info.loc['Median Household Assessed Value ($)','value']
        assessed_val_change = assessed_val_change + edit_df_basic_info.loc['# business in flood plain','value'] * edit_df_basic_info.loc['Median Commercial Assessed Value ($)','value']
        assessed_val_change = assessed_val_change * percent_value_change / 100
        property_tax_rev_change = assessed_val_change * percent_tax_rate_municipal / 100
        total_rev_change = general_rev_change + property_tax_rev_change

        result_rev = ['Per-Capita Revenues','Change in Residents','Change in residential revenues',
                      'Per-Worker Revenues','Change in Workers','Change in non-residential revenues',
                      'Change in General Revenues',
                      'Total Assessed Value Change','Change in Property Tax Revenues',
                      'Change in Total Revenues']
        result_rev = pd.DataFrame({'value':[residential_percap_rev, total_change_pop, residential_rev_change, 
                                            nonresidential_percap_rev, total_change_job, nonresidential_rev_change,
                                            general_rev_change,
                                            assessed_val_change, property_tax_rev_change,
                                            total_rev_change]},
                                  index=result_rev)

        st.dataframe(result_rev,
                     column_config={col_i: st.column_config.NumberColumn(format = '%i') for col_i in ['value'] })
        st.text(f'*Municipal Purpose Tax Rate = {percent_tax_rate_municipal}%')
        
        # except: 
        #     st.text('data format error.')

        
if total_cost_change != None and total_rev_change != None:
    
    st.divider()
    
    st.markdown("## Simulation Results")
    st.sidebar.markdown("## Simulation Results")
    
    st.markdown("### Pre-scenario Net Fiscal Impact (Absolute)")
    st.sidebar.markdown("### Pre-scenario Net Fiscal Impact (Absolute)")
    
    dt_pre_scenario = ['General Revenues','Property Tax Revenues','Total Revenues','Total Expenditures','Net Impact']
    
    dt_pre_scenario_gen_rev = import_rev_df['Residential'].sum()+import_rev_df['Non-Residential'].sum()
    dt_pre_scenario_prop_tax = edit_df_basic_info.loc['Total Assessed Value ($)','value'] * percent_tax_rate_municipal/100
    dt_pre_scenario_tot_rev = dt_pre_scenario_prop_tax + dt_pre_scenario_gen_rev
    dt_pre_scenario_tot_exp = import_exp_df['Residential'].sum()+import_exp_df['Non-Residential'].sum()
    
    dt_pre_scenario = pd.DataFrame({'value':[dt_pre_scenario_gen_rev, dt_pre_scenario_prop_tax,
                                              dt_pre_scenario_tot_rev,
                                              dt_pre_scenario_tot_exp,
                                              dt_pre_scenario_tot_rev - dt_pre_scenario_tot_exp]},
                                    index = dt_pre_scenario)
    
    st.dataframe(dt_pre_scenario, 
                 column_config={col_i: st.column_config.NumberColumn(format = "%i") for col_i in ['value'] })
    
    st.markdown("### Population")
    st.sidebar.markdown("### Population")
    
    dt_final_pop = ['Population Change','Worker Change']
    dt_final_pop = pd.DataFrame({'value':[result_PopChange.loc['Total Change in Residents', 'value'],
                                          result_PopChange.loc['Total Change in Number of Workers', 'value'] ] },
                                index = dt_final_pop)
    
    st.dataframe(dt_final_pop,
                 column_config={col_i: st.column_config.NumberColumn(format = "%i") for col_i in ['value'] })
    
    st.markdown("### Expenditure")
    st.sidebar.markdown("### Expenditure")
    
    dt_final_exp_new = dt_pre_scenario_tot_exp + total_cost_change
    
    dt_final_exp = ['Total Expenditures', 'Change in Total Expenditures', 'New Total Expenditures']
    dt_final_exp = pd.DataFrame({'value':[dt_pre_scenario_tot_exp, total_cost_change, dt_final_exp_new] },
                                index = dt_final_exp)
    st.dataframe(dt_final_exp,
                 column_config={col_i: st.column_config.NumberColumn(format = "%i") for col_i in ['value'] })
    
    st.markdown("### Assessed Property Value")
    st.sidebar.markdown("### Assessed Property Value")
    
    PropVal_change_r = edit_df_basic_info.loc['# homes in flood plain','value'] * edit_df_basic_info.loc['Median Household Assessed Value ($)','value']
    PropVal_change_r = PropVal_change_r*percent_value_change/100
    PropVal_change_nr = edit_df_basic_info.loc['# business in flood plain','value'] * edit_df_basic_info.loc['Median Commercial Assessed Value ($)','value']
    PropVal_change_nr = PropVal_change_nr*percent_value_change/100
    PropVal_change_total = PropVal_change_r + PropVal_change_nr
    PropVal_new = edit_df_basic_info.loc['Total Assessed Value ($)','value'] + PropVal_change_total
    
    dt_final_PropVal = ['Residential Assessed Value Change', 'Commercial Assessed Value Change', 'Total Assessed Value Change (delta)',
                        'New Total Assessed Value']
    dt_final_PropVal = pd.DataFrame({'value':[PropVal_change_r, PropVal_change_nr, PropVal_change_total, PropVal_new] },
                                    index = dt_final_PropVal)
    st.dataframe(dt_final_PropVal,
                 column_config={col_i: st.column_config.NumberColumn(format = "%i") for col_i in ['value'] })
    
    st.markdown("### Revenue")
    st.sidebar.markdown("### Revenue")
    
    dt_final_rev_general_change = result_rev.loc['Change in General Revenues','value']
    dt_final_rev_general = dt_pre_scenario_gen_rev + dt_final_rev_general_change
    
    dt_final_rev_property_change = result_rev.loc['Change in Property Tax Revenues','value']
    dt_final_rev_property = dt_pre_scenario_prop_tax + dt_final_rev_property_change
    
    dt_final_rev_total_change = dt_final_rev_general_change + dt_final_rev_property_change
    dt_final_rev_total = dt_pre_scenario_tot_rev + dt_final_rev_total_change
        
    dt_final_rev = ['General Revenues', 'Change in General Revenues', 'New General Revenues',
                    'Property Tax Revenues', 'Change in Property Tax Revenues', 'New Property Tax Revenues',
                    'Total Revenues', 'Change in Total Revenues', 'New Total Revenues']
    dt_final_rev = pd.DataFrame({'value':[dt_pre_scenario_gen_rev, dt_final_rev_general_change, dt_final_rev_general, 
                                          dt_pre_scenario_prop_tax, dt_final_rev_property_change, dt_final_rev_property,
                                          dt_pre_scenario_tot_rev, dt_final_rev_total_change, dt_final_rev_total] },
                                    index = dt_final_rev)
    st.dataframe(dt_final_rev,
                 column_config={col_i: st.column_config.NumberColumn(format = "%i") for col_i in ['value'] })
    
    st.markdown("### Results")
    st.sidebar.markdown("### Results")
    
    st.markdown("#### Net Fiscal Impact on Municipal Budget (Change)")
    st.sidebar.markdown("#### Net Fiscal Impact on Municipal Budget (Change)")
    
    net_impact_change = dt_final_rev_total_change - total_cost_change
    net_impact_abs = dt_final_rev_total - dt_final_exp_new
    
    dt_final_net_change = ['Change in Total Revenues', 'Change in Expenditure', 'Net Fiscal Impact on Municipal Budget (Change)',
                           'New Total Revenues', 'New Total Expenditures', 'Net Fiscal Impact on Municipal Budget (Absolute)']
    dt_final_net_change = pd.DataFrame({'value':[dt_final_rev_total_change, total_cost_change, net_impact_change,
                                                dt_final_rev_total, dt_final_exp_new, net_impact_abs] },
                                       index = dt_final_net_change)
    
    # st.dataframe(dt_final_net_change,
    #              column_config={col_i: st.column_config.NumberColumn(format = "%i") for col_i in ['value'] })
    
    net_change_percent_rev = dt_final_rev_total_change / dt_pre_scenario_tot_rev * 100
    net_change_percent_exp = total_cost_change / dt_pre_scenario_tot_exp * 100
    
    df_final_pivot = ['Revenue','Expenditure','Net Fiscal Impact']
    df_final_pivot = pd.DataFrame({'Previous': [dt_pre_scenario_tot_rev, dt_pre_scenario_tot_exp, dt_pre_scenario_tot_rev-dt_pre_scenario_tot_exp],
                                   'New': [dt_final_rev_total, dt_final_exp_new, net_impact_abs], 
                                   'Change': [dt_final_rev_total_change, total_cost_change, net_impact_change],
                                   '% Change': [net_change_percent_rev, net_change_percent_exp, None]}, 
                                 index = df_final_pivot)
    
    df_final_pivot_ccfg = {col_i: st.column_config.NumberColumn(format = "%i") for col_i in ['Previous','Change','New'] }
    df_final_pivot_ccfg = df_final_pivot_ccfg | {col_i: st.column_config.NumberColumn(format = "%.1f%%") for col_i in ['% Change'] }
    
    st.dataframe(df_final_pivot,
                 column_config = df_final_pivot_ccfg)

saved_sims = pd.DataFrame()
saved_sims_idx=0

if total_cost_change != None and total_rev_change != None:
    
    sim_save_div_0.divider()
    sim_result_title.markdown("### Simulation Result - Summary")
    # sim_result_title_sidebar.sidebar.markdown("### Simulation Result - Summary")
    sim_save_div_1.divider()
    
    sim_result_summary.dataframe(df_final_pivot,
                                 column_config = df_final_pivot_ccfg)
        
