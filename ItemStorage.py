import pandas as pd
import os

class ItemStorage:
    def __init__(self, file_path=None, value=None, itemClassName=None):
        self.file_path = file_path
        _, extension = os.path.splitext(self.file_path)
        self.extension = extension
        
        self.columns = value.attributes if value and type(value) != list else value[0].attributes if value and type(value) == list else itemClassName.attributes if itemClassName else None
        
         # Create the DataFrame with 'columns' if the file doesn't exist
        if not os.path.isfile(self.file_path) and self.columns:
            self.data = pd.DataFrame(columns=self.columns)
            self.save_data()
        else:
            if self.extension == '.csv':
                self.data = pd.read_csv(self.file_path, encoding='utf-8-sig')
            elif self.extension == '.xlsx':
                self.data = pd.read_excel(self.file_path)
            else:
                print("Error : L'extension n'est ni .csv ni .xlsx")
            if not self.columns:
                self.columns = list(self.data.columns)
        
        # Insert the value if provided
        if value:
            if isinstance(value, list):
                self.insert_items(value)
            else:
                self.insert_item(value)
                
    def save_data(self):
        _, extension = os.path.splitext(self.file_path)
        self.extension = extension
        if self.extension == '.csv':
            self.data.to_csv(self.file_path, index=False, encoding='utf-8-sig')
        elif self.extension == '.xlsx':
            self.data.to_excel(self.file_path, index=False)
        else:
            print("Error : L'extension n'est ni .csv ni .xlsx")
            
    def insert_item(self, item):
        if not self.columns :
            self.columns = item.attributes
            self.data = pd.DataFrame(columns=self.columns)
            
        data = item.to_dict()
        # Assume data is a dictionary with keys 'key_words', 'category', 'description'
        new_data = pd.DataFrame([data], columns=self.columns)
        self.data = pd.concat([self.data, new_data], ignore_index=True)
        self.save_data()
        
    def insert_items(self, items):
        if not self.columns :
            self.columns = items[0].attributes
            self.data = pd.DataFrame(columns=self.columns)
            
        # Assume items is a list of dictionaries, where each dictionary represents a row
        items = [item.to_dict() for item in items]
        new_data = pd.DataFrame(items, columns=self.columns)
        self.data = pd.concat([self.data, new_data], ignore_index=True)
        self.save_data()

    def get_list_of_dicts(self):
        return self.data.to_dict(orient='records')