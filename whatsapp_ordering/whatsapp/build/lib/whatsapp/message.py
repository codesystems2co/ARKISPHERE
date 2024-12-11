from . message_template import template

class message:
    #always used in message body
    messaging_product = None
    recipient_type = None
    to_phone_number = None
    
    # message type and their objects separated
    _type = None
    _template = None

    _preview_url = None
    _text = None
    _interactive = None

    def __init__(self):
        self._template = template()
        self._template.components = []

    def body(self):
        body = {
                    "messaging_product": self.messaging_product,
               }

        if self.recipient_type:
            body['recipient_type'] = self.recipient_type
        if self.to_phone_number:
            body['to'] = self.to_phone_number
        if self.to_phone_number:
            body['type'] = self._type
        if self._type == 'template':
            body['template'] = self._template.body()
        if self._type == 'interactive':
            body['interactive'] = self._interactive
        if self._type == 'text':
            text = {}
            if self._preview_url:
                text['preview_url'] = self._preview_url
            text['body'] = self._text
            body[self._type] = text
        
        return body
