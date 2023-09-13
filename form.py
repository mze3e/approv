import streamlit as st
import uuid
from datetime import time, datetime, date
from utils import center_align_string, round_up_to_nearest_5
import yaml
import pandas as pd

class Form:
    def __init__(self, st, form_config):
        self.st = st
        self.form_config = form_config
        self.form,self.actions = self._get_config()

    def _get_config(self):
        # Read from the YAML file
        form = {}
        actions = {}

        if type(self.form_config) is dict():
            pass
        else:
            with open('form.yaml', 'r') as file:
                self.form_config = yaml.safe_load(file)
        
        try:
            form = self.form_config['form']
        except KeyError as e:
            raise e
        
        try:
            actions=self.form_config['actions']
        except KeyError as e:
            raise e
        
        return form,actions
    
    def _is_disabled(self, item):
        try:
            return not self.form[item]['editable']
        except:
            return False
    
    def _default_value(self, item):
        try:
            return self.form[item]['default']
        except:
            if self.form[item]['type'] in ['checkbox','toggle']:
                return False
            elif self.form[item]['type'] in ['radio','selectbox']:
                return 0 #index
            elif self.form[item]['type'] == 'slider':
                return self.form[item]['min_value']
            elif self.form[item]['type'] in ['multiselect']:
                return None
            elif 'options' in self.form[item]:
                return self.form[item]['options'][0]
            elif self.form[item]['type'] == 'number_input':
                return 0.0
            elif self.form[item]['type'] == 'date_input':
                return date.today()
            elif self.form[item]['type'] == 'time_input':
                 return datetime.time(datetime.now())
            elif self.form[item]['type'] == 'color_picker':
                 return '#ffffff'
            elif self.form[item]['type'] == 'dataframe':
                 return pd.DataFrame(self.form[item]['columns']) 
            else:
                return ""

    def get_form(self,data=None):

        for item in self.form.keys():
            try:
                default_value = data[item]
                if self.form[item]['type'] in ['radio','selectbox']:
                    default_value = self.form[item]['options'].index(default_value) #index
                if self.form[item]['type'] in ['date_input']:
                    default_value = datetime.strptime(default_value, "%Y-%m-%d")
                if self.form[item]['type'] in ['time_input']:
                    # Split the string into hours, minutes, and seconds
                    hours, minutes, seconds = map(int, default_value.split(':'))
                    default_value = time(hours, minutes, seconds)
            except:
                default_value = self._default_value(item)

            if self.form[item]['type'] == 'checkbox':
                st.checkbox(f"{self.form[item]['title']}", 
                            value=default_value, 
                            key=item, 
                            disabled=self._is_disabled(item)
                            )

            if self.form[item]['type'] == 'toggle':
                st.toggle(f"{self.form[item]['title']}",
                          key=item, 
                          disabled=self._is_disabled(item),
                          value=default_value)

            if self.form[item]['type'] == 'radio':
                st.radio(f"{self.form[item]['title']}", 
                         self.form[item]['options'], 
                         key=item, 
                         disabled=self._is_disabled(item),
                         index=default_value)
            
            if self.form[item]['type'] == 'selectbox':
                st.selectbox(f"{self.form[item]['title']}",
                             options=self.form[item]['options'], 
                             key=item, 
                             disabled=self._is_disabled(item),
                             index=default_value)
            
            if self.form[item]['type'] == 'multiselect':
                st.multiselect(f"{self.form[item]['title']}", 
                               options=self.form[item]['options'], 
                               key=item, 
                               disabled=self._is_disabled(item),
                               default=default_value)

            if self.form[item]['type'] == 'slider':
                st.write('Slider')
                st.write(self.form[item]['min_value'])
                st.write(self.form[item]['max_value'])
                st.write(default_value)
                
                st.slider(f"{self.form[item]['title']}", 
                          min_value=self.form[item]['min_value'], 
                          max_value=self.form[item]['max_value'], 
                          step=self.form[item]['step'], 
                          key=item, 
                          disabled=self._is_disabled(item),
                          value=default_value)
                
                # st.slider(f"range {item}", 0.0, 100.0, key=item+'range', disabled=self._is_disabled(item),
                #             value=default_value)
                # st.slider("Schedule your appointment:", value=(time(11, 30), time(12, 45)), key=item+"time", disabled=self._is_disabled(item))
                #             #value=default_value)
                # st.slider("When do you start?", value=datetime(2020, 1, 1, 9, 30), format="DD/MM/YYYY - hh:mm", key=item+"datetime", disabled=self._is_disabled(item))
                #             #value=default_value)

            if self.form[item]['type'] == "select_slider":
                st.select_slider(label=f"{self.form[item]['title']}", options=['red', 'orange', 'yellow', 'green', 'blue', 'indigo', 'violet'], key=item, disabled=self._is_disabled(item))#,
                            #value=default_value)
            
            if self.form[item]['type'] == 'text_input':
                st.text_input(f"{self.form[item]['title']}", key=item, disabled=self._is_disabled(item),
                            value=default_value)
                
            if self.form[item]['type'] == 'number_input':
                st.number_input(f"{self.form[item]['title']}", key=item, disabled=self._is_disabled(item),
                            value=default_value)
            
            if self.form[item]['type'] == 'text_area':
                st.text_area(f"{self.form[item]['title']}", key=item, disabled=self._is_disabled(item),
                            value=default_value)

            if self.form[item]['type'] == 'date_input':
                st.date_input(f"{self.form[item]['title']}", 
                              key=item, 
                              disabled=self._is_disabled(item),
                              format="DD/MM/YYYY",
                              value=default_value)
            
            if self.form[item]['type'] == 'time_input':
                st.time_input(f"{self.form[item]['title']}", 
                              key=item, 
                              disabled=self._is_disabled(item),
                              value=default_value)

            if self.form[item]['type'] == 'file_uploader':
                st.file_uploader(f"{self.form[item]['title']}", 
                                 key=item, 
                                 disabled=self._is_disabled(item))

            if self.form[item]['type'] == 'camera_input':
                st.camera_input(f"{self.form[item]['title']}", 
                                key=item, 
                                disabled=self._is_disabled(item))

            if self.form[item]['type'] == 'color_picker':
                st.color_picker(f"{self.form[item]['title']}", 
                                key=item, 
                                disabled=self._is_disabled(item),
                                value=default_value)
            if self.form[item]['type'] == 'dataframe':
                pass

        def on_submit(button_key):
            st.session_state.submitted_by = button_key
        
        ncol = 5
        cols = st.columns(ncol)
        
        for i, x in enumerate(cols):
            try:
                item = list(self.actions.keys())[i]
                x.button(f"{self.actions[item]['title']}", key=item, on_click=on_submit, args=[item], use_container_width=True)
            except:
                break

    def get_form_data(self):
        values = {}
        if 'submitted_by' in st.session_state:
            for item in self.form:
                if item in st.session_state:
                    values[item] = st.session_state[item]
            
            values['actions']={}

            for item in self.actions:
                if item in st.session_state:
                    values['actions'][item] = st.session_state[item]

            values['action']=st.session_state.submitted_by

            return values
        
        else:
            return None