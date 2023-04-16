from replit import db
from flask import Flask, render_template

app = Flask(__name__)

#root --> '/'
#increment --> '/incement'

# db = {'number': 0}



if 'number' not in db:
  db['number'] = 0


@app.route('/')
def home():
  #show takes in two parameter: page, and number
  return render_template('index.html', number = db['number'])

@app.route('/increment')
def increment():
  db['number'] += 1
  return render_template('index.html', number = db['number'])


@app.route('/decrement')
def decrement():
  if db['number'] >= 1:
    db['number'] -= 1
  else:
    db['number'] == db['number']
  return render_template('index.html', number = db['number'])
app.run(host='0.0.0.0', port=81)