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
        self.form_fields,self.actions,self.permissions= self._get_config()

    def _get_config(self):
        # Read from the YAML file
        form_fields = {}
        actions = {}

        if type(self.form_config) is dict():
            pass
        else:
            with open('form.yaml', 'r') as file:
                self.form_config = yaml.safe_load(file)
        
        try:
            form_fields = self.form_config['form']['fields']
        except KeyError as e:
            raise e
        
        try:
            actions=self.form_config['form']['actions']
        except KeyError as e:
            raise e
        
        try:
            permissions=self.form_config['form']['permissions']
        except KeyError as e:
            raise e

        return form_fields,actions,permissions
    
    def _is_disabled(self, item, user_roles):
        try:
            disabled_field = not self.form_fields[item]['editable']
        except:
            disabled_field = False

        try:
            for role in self.permissions[item]:
                if role in user_roles:
                    disabled_perm = False
                else:
                    disabled_perm = True
                    break
        except:
            disabled_perm = False

        return disabled_field or disabled_perm

    def _default_value(self, item):
        try:
            return self.form_fields[item]['default']
        except:
            if self.form_fields[item]['type'] in ['checkbox','toggle']:
                return False
            elif self.form_fields[item]['type'] in ['radio','selectbox']:
                return 0 #index
            elif self.form_fields[item]['type'] == 'slider':
                return self.form_fields[item]['min_value']
            elif self.form_fields[item]['type'] in ['multiselect']:
                return None
            elif 'options' in self.form_fields[item]:
                return self.form_fields[item]['options'][0]
            elif self.form_fields[item]['type'] == 'number_input':
                return 0.0
            elif self.form_fields[item]['type'] == 'date_input':
                return date.today()
            elif self.form_fields[item]['type'] == 'time_input':
                 return datetime.time(datetime.now())
            elif self.form_fields[item]['type'] == 'color_picker':
                 return '#ffffff'
            elif self.form_fields[item]['type'] == 'dataframe':
                pass
                 #return pd.DataFrame(self.form_fields[item]['columns']) 
            else:
                return ""

    def get_form(self,data=None, user=None, actions=None):

        for item in self.form_fields.keys():
            try:
                default_value = data[item]
                if self.form_fields[item]['type'] in ['radio','selectbox']:
                    default_value = self.form_fields[item]['options'].index(default_value) #index
                if self.form_fields[item]['type'] in ['date_input']:
                    default_value = datetime.strptime(default_value, "%Y-%m-%d")
                if self.form_fields[item]['type'] in ['time_input']:
                    # Split the string into hours, minutes, and seconds
                    hours, minutes, seconds = map(int, default_value.split(':'))
                    default_value = time(hours, minutes, seconds)
            except:
                default_value = self._default_value(item)

            try:
                field_disabled = self._is_disabled(item,user)
            except:
                field_disabled = False
            
            if self.form_fields[item]['type'] == 'checkbox':
                st.checkbox(f"{self.form_fields[item]['title']}", 
                            value=default_value, 
                            key=item, 
                            disabled=field_disabled
                            )

            if self.form_fields[item]['type'] == 'toggle':
                st.toggle(f"{self.form_fields[item]['title']}",
                          key=item, 
                          disabled=field_disabled,
                          value=default_value)

            if self.form_fields[item]['type'] == 'radio':
                st.radio(f"{self.form_fields[item]['title']}", 
                         self.form_fields[item]['options'], 
                         key=item, 
                         disabled=field_disabled,
                         index=default_value)
            
            if self.form_fields[item]['type'] == 'selectbox':
                st.selectbox(f"{self.form_fields[item]['title']}",
                             options=self.form_fields[item]['options'], 
                             key=item, 
                             disabled=field_disabled,
                             index=default_value)
            
            if self.form_fields[item]['type'] == 'multiselect':
                st.multiselect(f"{self.form_fields[item]['title']}", 
                               options=self.form_fields[item]['options'], 
                               key=item, 
                               disabled=field_disabled,
                               default=default_value)

            if self.form_fields[item]['type'] == 'slider':
                st.write('Slider')
                st.write(self.form_fields[item]['min_value'])
                st.write(self.form_fields[item]['max_value'])
                st.write(default_value)
                
                st.slider(f"{self.form_fields[item]['title']}", 
                          min_value=self.form_fields[item]['min_value'], 
                          max_value=self.form_fields[item]['max_value'], 
                          step=self.form_fields[item]['step'], 
                          key=item, 
                          disabled=field_disabled,
                          value=default_value)
                
                # st.slider(f"range {item}", 0.0, 100.0, key=item+'range', disabled=field_disabled,
                #             value=default_value)
                # st.slider("Schedule your appointment:", value=(time(11, 30), time(12, 45)), key=item+"time", disabled=field_disabled)
                #             #value=default_value)
                # st.slider("When do you start?", value=datetime(2020, 1, 1, 9, 30), format="DD/MM/YYYY - hh:mm", key=item+"datetime", disabled=field_disabled)
                #             #value=default_value)

            if self.form_fields[item]['type'] == "select_slider":
                st.select_slider(label=f"{self.form_fields[item]['title']}", options=['red', 'orange', 'yellow', 'green', 'blue', 'indigo', 'violet'], key=item, disabled=field_disabled)#,
                            #value=default_value)
            
            if self.form_fields[item]['type'] == 'text_input':
                st.text_input(f"{self.form_fields[item]['title']}", key=item, disabled=field_disabled,
                            value=default_value)
                
            if self.form_fields[item]['type'] == 'number_input':
                st.number_input(f"{self.form_fields[item]['title']}", key=item, disabled=field_disabled,
                            value=default_value)
            
            if self.form_fields[item]['type'] == 'text_area':
                st.text_area(f"{self.form_fields[item]['title']}", key=item, disabled=field_disabled,
                            value=default_value)

            if self.form_fields[item]['type'] == 'date_input':
                st.date_input(f"{self.form_fields[item]['title']}", 
                              key=item, 
                              disabled=field_disabled,
                              format="DD/MM/YYYY",
                              value=default_value)
            
            if self.form_fields[item]['type'] == 'time_input':
                st.time_input(f"{self.form_fields[item]['title']}", 
                              key=item, 
                              disabled=field_disabled,
                              value=default_value)

            if self.form_fields[item]['type'] == 'file_uploader':
                st.file_uploader(f"{self.form_fields[item]['title']}", 
                                 key=item, 
                                 disabled=field_disabled)

            if self.form_fields[item]['type'] == 'camera_input':
                st.camera_input(f"{self.form_fields[item]['title']}", 
                                key=item, 
                                disabled=field_disabled)

            if self.form_fields[item]['type'] == 'color_picker':
                st.color_picker(f"{self.form_fields[item]['title']}", 
                                key=item, 
                                disabled=field_disabled,
                                value=default_value)
            if self.form_fields[item]['type'] == 'dataframe':
                pass

        def on_submit(button_key):
            st.session_state.submitted_by = button_key
        
        ncol = 5
        cols = st.columns(ncol)
        
        actions = self.actions if actions is None else actions
        for i, x in enumerate(cols):
            try:
                item = list(actions.keys())[i]
                x.button(f"{actions[item]['title']}", key=item, on_click=on_submit, args=[item], use_container_width=True)
            except:
                break

    def get_form_data(self):
        values = {}
        if 'submitted_by' in st.session_state:
            for item in self.form_fields:
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