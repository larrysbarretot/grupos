#encoding: utf-8
from wtforms import Form
from wtforms import StringField, RadioField, BooleanField, SelectField
from wtforms import validators

class NuevoParticipante(Form):
	nombre_completo = StringField('Nombre Completo',
		[
			validators.Required()
		])
	genero = RadioField(u'Género', choices=[('0', 'Femenino'), ('1', 'Masculino')], default='1')
	estatura = BooleanField('Alto')
	iglesia = SelectField('De la Iglesia')

class NuevaIglesia(Form):
	nombre_iglesia = StringField('Nombre Iglesia',
		[
			validators.Required()
		])