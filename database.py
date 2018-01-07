from flask import Flask
from flask import render_template
from flask import request
from flask import flash
from datetime import datetime
from flask_mysqldb import MySQL
import forms
import random
from random import shuffle
from flask import url_for
from flask import redirect

app = Flask(__name__)
app.secret_key='my_secret_key'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'ca17varones'
mysql = MySQL(app)

@app.before_request
def before_request():
	pass

def connection_execute(query):
	cur = mysql.connection.cursor()
	cur.execute(query)
	return cur

def all_rows(query):
	cur = connection_execute(query)
	return cur.fetchall()

def single_row(query):
	cur = connection_execute(query)
	return cur.fetchone()

# falta
def insert_row(query):
	cur = connection_execute(query)
	mysql.connection.commit()

@app.route('/')
def index():
	grupos = all_rows('''SELECT id, nombreGrupo FROM grupos''')
	#participantes = all_rows('''SELECT id, nombreCompleto, sexo, estatura, fechaRegistro, iglesias_id, grupos_id FROM participantes''')
	participantes = all_rows('''SELECT participantes.id, participantes.nombreCompleto, participantes.sexo, participantes.estatura, participantes.fechaRegistro, participantes.iglesias_id, participantes.grupos_id, iglesias.nombreIglesia FROM participantes JOIN iglesias ON iglesias.id = participantes.iglesias_id''')
	#return str(rv[0][1])
	return render_template('index.html', grupos=grupos, participantes=participantes)

@app.route('/generar')
def generar():
	participantes = all_rows('''SELECT nombreCompleto, sexo, estatura, iglesias_id FROM participantes''')
	x = [[participante] for participante in participantes]
	shuffle(x)
	cur = mysql.connection.cursor()
	cur.execute('''TRUNCATE TABLE participantes''')
	for a in x:
		nombre = a[0][0]
		genero = a[0][1]
		estatura = a[0][2]
		iglesia = a[0][3]
		grupo = obtenerGrupo(int(genero), int(estatura))
		fecha = datetime.now()
		maxid = single_row('''SELECT MAX(id) FROM participantes''')
		if str(maxid[0]) == 'None':
			last_id = 0
		else:
			last_id = maxid[0]
		cur.execute('''INSERT INTO participantes(id, nombreCompleto, sexo, estatura, fechaRegistro, iglesias_id, grupos_id) VALUES(%s, %s, %s, %s, %s, %s, %s)''', (last_id+1, nombre, int(genero), estatura, fecha, iglesia, grupo))
		mysql.connection.commit()

	success_message = u"Nuevos Grupos generados!"
	flash(success_message)
	return redirect('/')

@app.route('/participante', methods=['GET', 'POST'])
def participante():
	rv = all_rows('''SELECT id, nombreIglesia FROM iglesias''')
	nuevo_participante = forms.NuevoParticipante(request.form)
	nuevo_participante.iglesia.choices = [(g[0], g[1]) for g in rv]
	
	if request.method == 'POST':
		if nuevo_participante.validate():
			return "entro"
		nombre = nuevo_participante.nombre_completo.data
		genero = nuevo_participante.genero.data
		estatura = 1 if nuevo_participante.estatura.data == True else 0
		iglesia = nuevo_participante.iglesia.data
		grupo = obtenerGrupo(int(genero), int(estatura))
		fecha = datetime.now()
		maxid = single_row('''SELECT MAX(id) FROM participantes''')
		if str(maxid[0]) == 'None':
			last_id = 0
		else:
			last_id = maxid[0]
		cur = mysql.connection.cursor()
		cur.execute('''INSERT INTO participantes(id, nombreCompleto, sexo, estatura, fechaRegistro, iglesias_id, grupos_id) VALUES(%s, %s, %s, %s, %s, %s, %s)''', (last_id+1, nombre, int(genero), estatura, fecha, iglesia, grupo))
		mysql.connection.commit()
		#insert_row(consulta)
		success_message = u"{} Registrado!".format(nombre)
		flash(success_message)

	return render_template('nuevo_participante.html', form=nuevo_participante)

def obtenerGrupo(sexo, estatura):
	# cantidad de integrantes por sexo y estatura
	resultado = all_rows('''SELECT grupos.id, grupos.nombreGrupo, COUNT(participantes.id) AS NumeroDeVaronesAltos FROM participantes RIGHT JOIN grupos ON participantes.grupos_id=grupos.id AND participantes.sexo=sexo AND participantes.estatura=estatura GROUP BY nombreGrupo''')
	listaIdGrupos = gruposElegidos(resultado)
	# cantidad de integrantes en cada grupo
	integrantes = all_rows('''SELECT grupos.id, grupos.nombreGrupo, COUNT(participantes.id) AS NumeroDeIntegrantes FROM participantes RIGHT JOIN grupos ON participantes.grupos_id=grupos.id GROUP BY nombreGrupo''')
	listaIdGruposCompletos = gruposElegidos(integrantes)
	grupos = []
	for x in listaIdGruposCompletos:
		if x in listaIdGrupos:
			grupos.append(x)
	if len(grupos) == 0:
		grupoElegido = random.choice(listaIdGrupos)
	else:
		grupoElegido = random.choice(grupos)
	#print grupos
	return grupoElegido

def gruposElegidos(resultadoConsulta):
	#return str(resultadoConsulta[0][0])
	idGrupo = int(resultadoConsulta[0][0])
	cantidad = int(resultadoConsulta[0][2])
	gruposCandidatos = {}
	listaIdGrupos = []
	gruposCandidatos[idGrupo]=cantidad
	listaIdGrupos.append(idGrupo)
	for row in resultadoConsulta:
		i = int(row[0])
		j = int(row[2])
		if gruposCandidatos.has_key(i):
			continue
		if gruposCandidatos[idGrupo] == j:
			#agrego al diccionario
			gruposCandidatos[i] = j
			#print i
			listaIdGrupos.append(i)
		elif gruposCandidatos[idGrupo] > j:
			#remuevo el diccionario y agrego el nuevo minimo
			gruposCandidatos.clear()
			listaIdGrupos = []
			gruposCandidatos[i] = j
			listaIdGrupos.append(i)
			idGrupo = i
		else:
			continue
	return listaIdGrupos

@app.route('/iglesia', methods=['GET', 'POST'])
def iglesia():
	nueva_iglesia = forms.NuevaIglesia(request.form)
	if request.method == 'POST' and nueva_iglesia.validate():
		nombre = nueva_iglesia.nombre_iglesia.data
		maxid = single_row('''SELECT MAX(id) FROM iglesias''')
		if str(maxid[0]) == 'None':
			last_id = 0
		else:
			last_id = maxid[0]
		cur = mysql.connection.cursor()
		cur.execute('''INSERT INTO iglesias(id, nombreIglesia) VALUES(%s, %s)''', (last_id+1, nombre))
		mysql.connection.commit()
		success_message = u"{} Registrada!".format(nombre)
		flash(success_message)

	return render_template('nueva_iglesia.html', form=nueva_iglesia)

if __name__ == '__main__':
	app.run(debug=True, port=5001, host="192.168.0.234")