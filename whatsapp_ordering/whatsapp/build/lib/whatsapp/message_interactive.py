from . message_template_component import template_component

class template:
    
    name = None
    lenguage_code = None
    components = []
    _template_component = None

    def new_component(self):
        self._template_component = template_component()
        self._template_component.parameters = []
    
    def add_component(self):
        self.components.append(self._template_component)
    
    def body(self):
        body = {
                    "name": self.name,
                    "language":{'code':self.lenguage_code},
               } 
        if len(self.components) > 0:
            body['components'] = []
            for component in self.components:
                body['components'].append(component.body())
        return body