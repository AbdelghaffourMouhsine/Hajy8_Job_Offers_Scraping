class Item:
    attributes = ['index', 'company_name', 'company_size', 'company_linkedin_url', 'Secteur', 'Spécialisations', 'Profile_name', 'Profile_role',
                   'Profile_linkedin', 'job_source', 'key_words', 'job_title', 'job_description', 'job_url',

                  # Columns to added
                  'phones', 'emails', 'addresses',
                  # 'linkedin', 
                  'profiles', 'profile_name', 'profile_description', 'profile_url',
                  
                  'profile_address', 'country',
                  
                  'linkedin_about_info', 'about téléphone', 'about taille de l’entreprise',
                  'about page vérifiée', 'about site web','about spécialisations','about secteur','about siège social','about fondée en','about company_size',
                  'about vue d’ensemble', 'min_size', 'max_size']
    
    def __init__(self, dict=None):
        for attribute in self.attributes:
            setattr(self, attribute, None)
        if dict:
            for attr_name, attr_value in self.__dict__.items():
                setattr(self, attr_name, dict.get(attr_name))
            
    def init_from_dict(self, dict):
        for attr_name, attr_value in self.__dict__.items():
            setattr(self, attr_name, dict.get(attr_name))

    def to_dict(self):
        return self.__dict__
        
    def __str__(self):
        return str(self.to_dict())