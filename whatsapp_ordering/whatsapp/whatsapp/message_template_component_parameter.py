class template_component_parameter:
    
    _type = None

    # for type text
    text = None 
    coupon_code = None
    link = None

    def body(self):
        body = {
                    'type': self._type,
               }    
          
        if  self._type == 'text':
            body[self._type] = self.text
        
        if  self._type == 'coupon_code':
            body[self._type] = self.coupon_code

        if  self._type == 'image':
            body[self._type] = {'link': self.link}

        return body