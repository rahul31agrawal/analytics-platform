from flask_appbuilder.fieldwidgets import BS3TextFieldWidget


class BS3TextFieldROWidget(BS3TextFieldWidget):
    def __call__(self, field, **kwargs):
        kwargs['readonly'] = 'true'
        return super(BS3TextFieldROWidget, self).__call__(field,
                                                          **kwargs)