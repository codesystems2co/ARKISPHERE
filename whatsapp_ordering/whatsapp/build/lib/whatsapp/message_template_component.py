from . message_template_component_parameter import template_component_parameter

class template_component:
    
    _type = None
    _name = None
    # for buttons..
    _sub_type= None
    _index = None

    parameters = []
    _template_component_parameter = None

    def new_parameter(self):
        self._template_component_parameter = template_component_parameter()        
    
    def add_parameter(self):
        self.parameters.append(self._template_component_parameter)
    
    def body(self):
        body = {'type':self._type}

        if self._sub_type:
            body['sub_type'] = self._sub_type
            body['index'] = self._index
            
        if len(self.parameters) > 0:
            body['parameters'] = []
            for parameter in self.parameters:
                body['parameters'].append(parameter.body())
        return body