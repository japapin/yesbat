from flask import Flask, render_template, request, redirect, url_for, session, flash
import pandas as pd
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Usuários fixos
users = {
    "Admin": {"password": "Martins2025@", "role": "admin"},
    "Agenda": {"password": "Martins2025", "role": "viewer"}
}

class User(UserMixin):
    def __init__(self, username):
        self.id = username
        self.role = users[username]['role']

@login_manager.user_loader
def load_user(user_id):
    if user_id in users:
        return User(user_id)
    return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username]['password'] == password:
            user = User(username)
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Credenciais inválidas.')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST' and session.get('role') == 'admin':
        file = request.files['file']
        if file:
            file.save(os.path.join('app/uploads', 'agendamentos.xlsx'))
            flash('Relatório carregado com sucesso.')
            return redirect(url_for('index'))

    try:
        df = pd.read_excel(os.path.join('app/uploads', 'agendamentos.xlsx'))
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce').dt.date
    except:
        df = pd.DataFrame()

    filiais = df['Filial'].dropna().unique().tolist() if not df.empty else []

    return render_template('index.html', filiais=filiais, df=df.to_dict(orient='records'))

@app.route('/filial/<filial>')
@login_required
def filial_dashboard(filial):
    df = pd.read_excel(os.path.join('app/uploads', 'agendamentos.xlsx'))
    df['Data'] = pd.to_datetime(df['Data'], errors='coerce').dt.date
    df_filial = df[df['Filial'] == filial]

    total_pallets = df_filial['Pallet'].sum()
    fornecedores = df_filial['Fornecedor'].unique().tolist()
    operacoes = df_filial['Operação'].value_counts(normalize=True) * 100

    return render_template('filial.html',
                           filial=filial,
                           total_pallets=total_pallets,
                           fornecedores=fornecedores,
                           operacoes=operacoes.to_dict())

if __name__ == '__main__':
    app.run(debug=True)
