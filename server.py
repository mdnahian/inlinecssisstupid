#!/usr/bin/python
from flask import Flask, request, render_template, url_for
from werkzeug.utils import secure_filename
from bs4 import BeautifulSoup
from urllib import urlopen
import zipfile
import random
import time
import string
import os

app = Flask(__name__, static_url_path='')

UPLOAD_FOLDER = 'static/tmp/'
ALLOWED_EXTENSIONS = set(['html', 'htm'])

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def random_string():
	return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(8))


def createCSSFile(raw):
	
	styles = ''
	
	for key, value in raw.iteritems():
		styles += '.' + key + ' {\n'
		for style in value.split(';'):
			styles += '\t' + style + ';\n'
		styles = styles[:-2]
		styles += '\n}\n'

	filename = random_string() + '.css'
	with open(UPLOAD_FOLDER+filename, 'w') as cssfile:
		cssfile.write(styles)
		
	return filename


def createHTMLFile(raw, filename):
	with open(UPLOAD_FOLDER+filename, 'w') as htmlfile:
		htmlfile.write(str(raw))
	
	
def createZIPFile(cssfile, htmlfile):
	filename = random_string()+'.zip'
	zf = zipfile.ZipFile(UPLOAD_FOLDER+filename, mode='w')	
	try:
		zf.write(UPLOAD_FOLDER+cssfile)
		zf.write(UPLOAD_FOLDER+htmlfile)
	finally:
		zf.close()
	
	return filename
	

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/stupid', methods=['POST', 'GET'])
def stupid():
	if request.method == 'POST':
		return request.form['data']
	else:
		return 'Invalid Request'


@app.route('/upload', methods=['POST'])
def upload():
	if request.method == 'POST':
		error_msg = ''
		if 'file' not in request.files:
			print request.files
			error_msg = 'NO FILE FOUND'
		else:
			file = request.files['file']
			
			if file.filename == '':
				error_msg = 'NOT AN HTML FILE'
			elif file and allowed_file(file.filename):
				filename = secure_filename(file.filename)
				filename = random_string()+'.'+filename.rsplit('.', 1)[1]
				file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
				
				with open(UPLOAD_FOLDER+filename, 'r') as content_file:
					content = content_file.read()
	
				soup = BeautifulSoup(content, 'html.parser')
				
				tags = soup.findAll()
				
				styles = {}
				
				for tag in tags:

					style = tag.get('style')
					if style is not None:
						newClass = random_string()
						styles[newClass] = style
						del tag['style']
						
						currClass = tag.get('class')
						
						if currClass is None:
							currClass = ''
						else:
							currClass = currClass + ' '
						
						tag['class'] = currClass + newClass
				
				if len(styles.keys()) == 0:
					error_msg = 'NO INLINE CSS FOUND IN THIS FILE'
					os.remove(UPLOAD_FOLDER+filename)
					return '{"error":"'+error_msg+'"}'
				
				cssfile = createCSSFile(styles)
				stylesheet = soup.new_tag('link', rel='stylesheet', href=cssfile)
				
				head = soup.find('head')
				head.append(stylesheet)
				createHTMLFile(soup, filename)
				
				zipfile = createZIPFile(cssfile, filename)
				
				os.remove(UPLOAD_FOLDER+cssfile)
				os.remove(UPLOAD_FOLDER+filename)
				
				return '{"error":"", "filename":"'+url_for('static', filename='tmp/'+zipfile)+'"}'
		return '{"error":"'+error_msg+'"}'
	else:
		redirect('/')
	

if __name__ == '__main__':
	app.run(
		host='0.0.0.0',
		port=80
	)
				
				
				
			