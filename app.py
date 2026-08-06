import datetime
import hashlib
import os
import io
import csv
from sqlalchemy import func
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, jsonify, abort, Response
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user, login_required,
    logout_user, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash

# =====================================================================
# Configuração da Aplicação
# =====================================================================
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Ajuste para PostgreSQL no Render (substitui 'postgres://' por 'postgresql://')
db_url = os.getenv('DATABASE_URL', 'sqlite:///agenda_saas.db')
if db_url and db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Acesso restrito. Efetue login para continuar.'
login_manager.login_message_category = 'warning'

# =====================================================================
# Lista Oficial de Municípios - SC
# =====================================================================
CIDADES_SC = sorted([
    "Abdon Batista", "Abelardo Luz", "Agrolândia", "Agronômica", "Água Doce",
    "Águas de Chapecó", "Águas Frias", "Águas Mornas", "Alfredo Wagner", "Alto Bela Vista",
    "Anchieta", "Angelina", "Anita Garibaldi", "Anitápolis", "Antônio Carlos",
    "Apiúna", "Arabutã", "Araquari", "Araranguá", "Armazém",
    "Arroio Trinta", "Arvoredo", "Ascurra", "Atalanta", "Aurora",
    "Balneário Arroio do Silva", "Balneário Barra do Sul", "Balneário Camboriú", "Balneário Gaivota", "Balneário Piçarras",
    "Balneário Rincão", "Bandeirante", "Barra Bonita", "Barra Velha", "Bela Vista do Toldo",
    "Belmonte", "Benedito Novo", "Biguaçu", "Blumenau", "Bocaina do Sul",
    "Bom Jardim da Serra", "Bom Jesus", "Bom Jesus do Oeste", "Bom Retiro", "Bombinhas",
    "Botuverá", "Braço do Norte", "Braço do Trombudo", "Brunópolis", "Brusque",
    "Caçador", "Caibi", "Calmon", "Camboriú", "Campo Alegre",
    "Campo Belo do Sul", "Campo Erê", "Campos Novos", "Canelinha", "Canoinhas",
    "Capão Alto", "Capinzal", "Capivari de Baixo", "Catanduvas", "Caxambu do Sul",
    "Celso Ramos", "Cerro Negro", "Chapadão do Lageado", "Chapecó", "Cocal do Sul",
    "Concórdia", "Cordilheira Alta", "Coronel Freitas", "Coronel Martins", "Correia Pinto",
    "Corupá", "Criciúma", "Cunha Porã", "Cunhataí", "Curitibanos",
    "Descanso", "Dionísio Cerqueira", "Dona Emma", "Doutor Pedrinho", "Entre Rios",
    "Ermo", "Erval Velho", "Faxinal dos Guedes", "Flor do Sertão", "Florianópolis",
    "Formosa do Sul", "Forquilhinha", "Fraiburgo", "Frei Rogério", "Galvão",
    "Garopaba", "Garuva", "Gaspar", "Governador Celso Ramos", "Grão Pará",
    "Gravatal", "Guabiruba", "Guaraciaba", "Guaramirim", "Guarujá do Sul",
    "Guatambú", "Herval d'Oeste", "Ibiam", "Ibicaré", "Ibirama",
    "Içara", "Ilhota", "Imaruí", "Imbituba", "Imbuia",
    "Indaial", "Iomerê", "Ipira", "Iporã do Oeste", "Ipuaçu",
    "Ipumirim", "Iraceminha", "Irani", "Irati", "Irineópolis",
    "Itá", "Itaiópolis", "Itajaí", "Itapema", "Itapiranga",
    "Itapoá", "Ituporanga", "Jaborá", "Jacinto Machado", "Jaguaruna",
    "Jaraguá do Sul", "Jardinópolis", "Joaçaba", "Joinville", "José Boiteux",
    "Jupiá", "Lacerdópolis", "Lages", "Laguna", "Lajeado Grande",
    "Laurentino", "Lauro Müller", "Lebon Régis", "Leoberto Leal", "Lindóia do Sul",
    "Lontras", "Luiz Alves", "Luzerna", "Macieira", "Mafra",
    "Major Gercino", "Major Vieira", "Maracajá", "Maravilha", "Marema",
    "Massaranduba", "Matos Costa", "Meleiro", "Mirim Doce", "Modelo",
    "Mondaí", "Monte Carlo", "Monte Castelo", "Morro da Fumaça", "Morro Grande",
    "Navegantes", "Nova Erechim", "Nova Itaberaba", "Nova Trento", "Nova Veneza",
    "Novo Horizonte", "Orleans", "Otacílio Costa", "Ouro", "Ouro Verde",
    "Paial", "Painel", "Palhoça", "Palma Sola", "Palmeira",
    "Palmitos", "Papanduva", "Paraíso", "Passo de Torres", "Passos Maia",
    "Paulo Lopes", "Pedras Grandes", "Penha", "Peritiba", "Pescaria Brava",
    "Petrolândia", "Pinhalzinho", "Pinheiro Preto", "Piratuba", "Planalto Alegre",
    "Pomerode", "Ponte Alta", "Ponte Alta do Norte", "Ponte Serrada", "Porto Belo",
    "Porto União", "Pouso Redondo", "Praia Grande", "Presidente Castello Branco", "Presidente Getúlio",
    "Presidente Nereu", "Princesa", "Quilombo", "Rancho Queimado", "Rio das Antas",
    "Rio do Campo", "Rio do Oeste", "Rio do Sul", "Rio dos Cedros", "Rio Fortuna",
    "Rio Negrinho", "Rio Rufino", "Riqueza", "Rodeio", "Romelândia",
    "Salete", "Saltinho", "Salto Veloso", "Sangão", "Santa Cecília",
    "Santa Helena", "Santa Rosa de Lima", "Santa Rosa do Sul", "Santa Terezinha", "Santa Terezinha do Progresso",
    "Santiago do Sul", "Santo Amaro da Imperatriz", "São Bento do Sul", "São Bernardino", "São Bonifácio",
    "São Carlos", "São Cristóvão do Sul", "São Domingos", "São Francisco do Sul", "São João Batista",
    "São João do Itaperiú", "São João do Oeste", "São João do Sul", "São Joaquim", "São José",
    "São José do Cedro", "São José do Cerrito", "São Lourenço do Oeste", "São Ludgero", "São Martinho",
    "São Miguel da Boa Vista", "São Miguel do Oeste", "São Pedro de Alcântara", "Saudades", "Schroeder",
    "Seara", "Serra Alta", "Siderópolis", "Sombrio", "Sul Brasil",
    "Taió", "Tangará", "Tigrinhos", "Tijucas", "Timbé do Sul",
    "Timbó", "Timbó Grande", "Três Barras", "Treviso", "Treze de Maio",
    "Treze Tílias", "Trombudo Central", "Tubarão", "Tunápolis", "Turvo",
    "União do Oeste", "Urubici", "Urupema", "Urussanga", "Vargeão",
    "Vargem", "Vargem Bonita", "Vidal Ramos", "Videira", "Vitor Meireles",
    "Witmarsum", "Xanxerê", "Xavantina", "Xaxim", "Zortéa"
])

# =====================================================================
# Utilitários de Interface e Segurança
# =====================================================================
def gerar_cor_por_cidade(nome_cidade: str) -> str:
    """Gera cor hexadecimal consistente em tom sóbrio (SaaS UI)."""
    hash_hex = hashlib.md5(nome_cidade.encode('utf-8')).hexdigest()
    r = int(hash_hex[0:2], 16) % 120 + 80
    g = int(hash_hex[2:4], 16) % 120 + 80
    b = int(hash_hex[4:6], 16) % 120 + 90
    return f'#{r:02x}{g:02x}{b:02x}'

cores_cidades = {cidade: gerar_cor_por_cidade(cidade) for cidade in CIDADES_SC}

def admin_required(f):
    """Decorador para restringir endpoints exclusivamente aos administradores."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.tipo != 'ADM':
            if request.path.startswith('/api/'):
                return jsonify({'status': 'erro', 'mensagem': 'Acesso negado. Permissão de administrador necessária.'}), 403
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

# =====================================================================
# Modelos de Banco de Dados
# =====================================================================
class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    senha_hash = db.Column(db.String(256), nullable=False)
    tipo = db.Column(db.String(20), nullable=False, default='Usuário')  # 'ADM' | 'Usuário'
    cidade = db.Column(db.String(100), nullable=True, index=True)
    criado_em = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Compromisso(db.Model):
    __tablename__ = 'compromissos'

    id = db.Column(db.Integer, primary_key=True)
    cidade = db.Column(db.String(100), nullable=False, index=True)
    data = db.Column(db.Date, nullable=False, index=True)
    hora = db.Column(db.Time, nullable=False)
    descricao = db.Column(db.String(200), nullable=False)
    checkin = db.Column(db.Boolean, default=False)
    criado_em = db.Column(db.DateTime, default=datetime.datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Usuario, int(user_id))

# =====================================================================
# Rotas de Autenticação e Navegação
# =====================================================================
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('painel_admin' if current_user.tipo == 'ADM' else 'painel_usuario'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        senha = request.form.get('senha', '')

        user = Usuario.query.filter_by(username=username).first()
        if user and check_password_hash(user.senha_hash, senha):
            login_user(user)
            flash(f'Sessão iniciada como {user.username}.', 'success')
            return redirect(url_for('painel_admin' if user.tipo == 'ADM' else 'painel_usuario'))
        
        flash('Credenciais inválidas. Verifique seu usuário e senha.', 'danger')
    return render_template('login.html')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        senha = request.form.get('senha', '')
        confirmar_senha = request.form.get('confirmar_senha', '')
        cidade = request.form.get('cidade', '')

        # Validação de campos obrigatórios
        if not username or not senha or not confirmar_senha:
            flash('Preencha todos os campos obrigatórios.', 'warning')
        elif len(username) < 3:
            flash('O nome de usuário deve ter pelo menos 3 caracteres.', 'warning')
        elif len(senha) < 4:
            flash('A senha deve ter no mínimo 4 caracteres.', 'warning')
        elif senha != confirmar_senha:
            flash('A confirmação de senha não confere.', 'warning')
        elif cidade not in CIDADES_SC:
            flash('Selecione uma cidade válida de Santa Catarina.', 'warning')
        else:
            # Verificação case‑insensitive
            usuario_existente = Usuario.query.filter(
                func.lower(Usuario.username) == username.lower()
            ).first()
            if usuario_existente:
                flash('Este nome de usuário já está registrado no sistema.', 'danger')
            else:
                novo_usuario = Usuario(
                    username=username,
                    senha_hash=generate_password_hash(senha),
                    tipo='Usuário',
                    cidade=cidade
                )
                db.session.add(novo_usuario)
                db.session.commit()
                flash('Conta criada com sucesso. Efetue login para continuar.', 'success')
                return redirect(url_for('login'))

    return render_template('cadastro.html', cidades=CIDADES_SC)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sessão encerrada com segurança.', 'info')
    return redirect(url_for('login'))

# =====================================================================
# Endpoints da API REST
# =====================================================================
@app.route('/api/cidades_com_eventos', methods=['GET'])
@login_required
def cidades_com_eventos():
    resultados = db.session.query(
        Compromisso.cidade,
        func.count(Compromisso.id).label('total')
    ).group_by(Compromisso.cidade).all()
    
    return jsonify({
        'status': 'sucesso',
        'dados': [{'cidade': r.cidade, 'total': r.total} for r in resultados]
    }), 200

@app.route('/api/stats', methods=['GET'])
@admin_required
def api_stats():
    total_compromissos = Compromisso.query.count()
    total_usuarios = Usuario.query.count()
    return jsonify({
        'status': 'sucesso',
        'dados': {
            'total_compromissos': total_compromissos,
            'total_usuarios': total_usuarios
        }
    }), 200

@app.route('/api/eventos', methods=['GET'])
@login_required
def api_eventos():
    cidade_filtro = request.args.get('cidade')
    
    if current_user.tipo == 'Usuário':
        cidade_filtro = request.args.get('cidade', current_user.cidade)

    query = Compromisso.query
    if cidade_filtro:
        query = query.filter_by(cidade=cidade_filtro)

    eventos = query.order_by(Compromisso.data, Compromisso.hora).all()
    eventos_formatados = []

    for e in eventos:
        cor = '#2d6a4f' if e.checkin else cores_cidades.get(e.cidade, '#4a5568')
        eventos_formatados.append({
            'id': e.id,
            'title': f"{e.hora.strftime('%H:%M')} - {e.descricao}",
            'start': f"{e.data.isoformat()}T{e.hora.strftime('%H:%M')}:00",
            'backgroundColor': cor,
            'borderColor': cor,
            'textColor': '#ffffff',
            'extendedProps': {
                'descricao': e.descricao,
                'checkin': e.checkin,
                'cidade': e.cidade
            }
        })

    return jsonify(eventos_formatados), 200

@app.route('/api/adicionar', methods=['POST'])
@admin_required
def adicionar_compromisso():
    data_json = request.get_json(silent=True) or {}
    cidade = data_json.get('cidade')
    data_iso = data_json.get('data')
    hora_str = data_json.get('hora')
    descricao = data_json.get('descricao', '').strip()

    if not all([cidade, data_iso, hora_str, descricao]):
        return jsonify({'status': 'erro', 'mensagem': 'Todos os campos são obrigatórios.'}), 400
    
    if cidade not in CIDADES_SC:
        return jsonify({'status': 'erro', 'mensagem': 'Cidade inválida. Selecione um município de Santa Catarina.'}), 400

    try:
        data_dt = datetime.datetime.strptime(data_iso, '%Y-%m-%d').date()
        hora_dt = datetime.datetime.strptime(hora_str, '%H:%M').time()
    except ValueError:
        return jsonify({'status': 'erro', 'mensagem': 'Formato de data ou hora inválido.'}), 400

    agora = datetime.datetime.now()
    evento_datetime = datetime.datetime.combine(data_dt, hora_dt)
    if evento_datetime < agora:
        return jsonify({'status': 'erro', 'mensagem': 'Não é permitido agendar eventos em horários passados.'}), 400

    conflito = Compromisso.query.filter_by(cidade=cidade, data=data_dt, hora=hora_dt).first()
    if conflito:
        return jsonify({'status': 'erro', 'mensagem': 'Já existe um evento agendado para este horário e município.'}), 409

    novo_compromisso = Compromisso(
        cidade=cidade,
        data=data_dt,
        hora=hora_dt,
        descricao=descricao,
        checkin=False
    )
    db.session.add(novo_compromisso)
    db.session.commit()

    return jsonify({'status': 'sucesso', 'mensagem': 'Compromisso criado com sucesso.', 'id': novo_compromisso.id}), 201

@app.route('/api/editar/<int:id>', methods=['PUT'])
@admin_required
def editar_compromisso(id):
    comp = db.session.get(Compromisso, id)
    if not comp:
        return jsonify({'status': 'erro', 'mensagem': 'Compromisso não encontrado.'}), 404

    data_json = request.get_json(silent=True) or {}
    cidade = data_json.get('cidade')
    data_iso = data_json.get('data')
    hora_str = data_json.get('hora')
    descricao = data_json.get('descricao', '').strip()

    if not all([cidade, data_iso, hora_str, descricao]):
        return jsonify({'status': 'erro', 'mensagem': 'Todos os campos são obrigatórios.'}), 400
    if cidade not in CIDADES_SC:
        return jsonify({'status': 'erro', 'mensagem': 'Cidade inválida.'}), 400

    try:
        data_dt = datetime.datetime.strptime(data_iso, '%Y-%m-%d').date()
        hora_dt = datetime.datetime.strptime(hora_str, '%H:%M').time()
    except ValueError:
        return jsonify({'status': 'erro', 'mensagem': 'Formato de data ou hora inválido.'}), 400

    agora = datetime.datetime.now()
    evento_datetime = datetime.datetime.combine(data_dt, hora_dt)
    if evento_datetime < agora:
        return jsonify({'status': 'erro', 'mensagem': 'Não é permitido reagendar para horários passados.'}), 400

    conflito = Compromisso.query.filter(
        Compromisso.cidade == cidade,
        Compromisso.data == data_dt,
        Compromisso.hora == hora_dt,
        Compromisso.id != id
    ).first()
    if conflito:
        return jsonify({'status': 'erro', 'mensagem': 'Já existe um evento neste horário e município.'}), 409

    comp.cidade = cidade
    comp.data = data_dt
    comp.hora = hora_dt
    comp.descricao = descricao
    db.session.commit()
    return jsonify({'status': 'sucesso', 'mensagem': 'Compromisso atualizado.'}), 200

@app.route('/api/excluir/<int:id>', methods=['DELETE'])
@admin_required
def excluir_compromisso(id):
    comp = db.session.get(Compromisso, id)
    if not comp:
        return jsonify({'status': 'erro', 'mensagem': 'Compromisso não encontrado.'}), 404

    db.session.delete(comp)
    db.session.commit()
    return jsonify({'status': 'sucesso', 'mensagem': 'Compromisso removido.'}), 200

@app.route('/api/checkin/<int:id>', methods=['POST'])
@login_required
def checkin(id):
    comp = db.session.get(Compromisso, id)
    if not comp:
        return jsonify({'status': 'erro', 'mensagem': 'Compromisso não encontrado.'}), 404

    comp.checkin = True
    db.session.commit()
    return jsonify({'status': 'sucesso', 'mensagem': 'Check-in confirmado com sucesso.'}), 200

@app.route('/api/exportar', methods=['GET'])
@login_required
def exportar_csv():
    cidade = request.args.get('cidade')
    if current_user.tipo == 'Usuário':
        cidade = cidade or current_user.cidade
    query = Compromisso.query
    if cidade:
        query = query.filter_by(cidade=cidade)
    compromissos = query.order_by(Compromisso.data, Compromisso.hora).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Cidade', 'Data', 'Hora', 'Descrição', 'Status'])
    for c in compromissos:
        writer.writerow([
            c.cidade,
            c.data.strftime('%d/%m/%Y'),
            c.hora.strftime('%H:%M'),
            c.descricao,
            'Confirmado' if c.checkin else 'Pendente'
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment;filename=agenda.csv'}
    )

# =====================================================================
# Endpoints de Gerenciamento de Usuários (Admin)
# =====================================================================
@app.route('/api/usuarios', methods=['GET'])
@admin_required
def api_usuarios():
    usuarios = Usuario.query.all()
    lista_usuarios = [{
        'id': u.id,
        'username': u.username,
        'tipo': u.tipo,
        'cidade': u.cidade or 'Todas (Global)'
    } for u in usuarios]
    return jsonify({'status': 'sucesso', 'dados': lista_usuarios}), 200

@app.route('/api/usuarios/adicionar', methods=['POST'])
@admin_required
def adicionar_usuario():
    dados = request.get_json(silent=True) or {}
    username = dados.get('username', '').strip()
    senha = dados.get('senha', '')
    tipo = dados.get('tipo', 'Usuário')
    cidade = dados.get('cidade', '') if tipo == 'Usuário' else None

    if not username or not senha:
        return jsonify({'status': 'erro', 'mensagem': 'Usuário e senha são obrigatórios.'}), 400

    if len(username) < 3:
        return jsonify({'status': 'erro', 'mensagem': 'O nome de usuário deve ter pelo menos 3 caracteres.'}), 400

    if len(senha) < 4:
        return jsonify({'status': 'erro', 'mensagem': 'A senha deve ter no mínimo 4 caracteres.'}), 400

    if Usuario.query.filter(func.lower(Usuario.username) == username.lower()).first():
        return jsonify({'status': 'erro', 'mensagem': 'Este nome de usuário já está em uso.'}), 409

    if tipo == 'Usuário' and not cidade:
        return jsonify({'status': 'erro', 'mensagem': 'Município obrigatório para perfil Usuário.'}), 400

    if cidade and cidade not in CIDADES_SC:
        return jsonify({'status': 'erro', 'mensagem': 'Cidade inválida. Selecione um município de Santa Catarina.'}), 400

    novo = Usuario(
        username=username,
        senha_hash=generate_password_hash(senha),
        tipo=tipo,
        cidade=cidade
    )
    db.session.add(novo)
    db.session.commit()
    return jsonify({'status': 'sucesso', 'mensagem': 'Usuário adicionado com sucesso.'}), 201

@app.route('/api/usuarios/excluir/<int:id>', methods=['DELETE'])
@admin_required
def excluir_usuario(id):
    user = db.session.get(Usuario, id)
    if not user:
        return jsonify({'status': 'erro', 'mensagem': 'Usuário não encontrado.'}), 404
    if user.username == 'admin' or user.id == current_user.id:
        return jsonify({'status': 'erro', 'mensagem': 'Não é possível excluir o administrador root ou sua conta atual.'}), 400
    
    db.session.delete(user)
    db.session.commit()
    return jsonify({'status': 'sucesso', 'mensagem': 'Usuário excluído.'}), 200

# =====================================================================
# Visões (Painéis Web)
# =====================================================================
@app.route('/usuario')
@login_required
def painel_usuario():
    if current_user.tipo != 'Usuário':
        return redirect(url_for('painel_admin'))
    return render_template('usuario.html', cidade=current_user.cidade, cidades=CIDADES_SC)

@app.route('/admin')
@admin_required
def painel_admin():
    return render_template('admin.html', cidades=CIDADES_SC)

@app.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    if request.method == 'POST':
        senha_atual = request.form.get('senha_atual', '')
        nova_senha = request.form.get('nova_senha', '')
        confirmacao = request.form.get('confirmacao', '')

        if not check_password_hash(current_user.senha_hash, senha_atual):
            flash('Senha atual incorreta.', 'danger')
        elif len(nova_senha) < 4:
            flash('A nova senha deve ter no mínimo 4 caracteres.', 'warning')
        elif nova_senha != confirmacao:
            flash('As novas senhas não conferem.', 'warning')
        else:
            current_user.senha_hash = generate_password_hash(nova_senha)
            db.session.commit()
            flash('Senha alterada com sucesso.', 'success')
            return redirect(url_for('perfil'))

    return render_template('perfil.html')

# =====================================================================
# Seed de Dados Iniciais
# =====================================================================
def criar_dados_iniciais():
    db.create_all()
    
    if not Usuario.query.first():
        admin = Usuario(
            username='admin',
            senha_hash=generate_password_hash('admin123'),
            tipo='ADM'
        )
        db.session.add(admin)

        exemplos = {
            'portouniao': 'Porto União',
            'florianopolis': 'Florianópolis',
            'joinville': 'Joinville',
            'blumenau': 'Blumenau',
            'chapeco': 'Chapecó'
        }
        for usuario_slug, nome_cidade in exemplos.items():
            u = Usuario(
                username=usuario_slug,
                senha_hash=generate_password_hash('1234'),
                tipo='Usuário',
                cidade=nome_cidade
            )
            db.session.add(u)
        db.session.commit()

    if not Compromisso.query.first():
        hoje = datetime.date.today()
        amanha = hoje + datetime.timedelta(days=1)
        
        exemplos_eventos = [
            Compromisso(
                cidade='Porto União',
                data=hoje,
                hora=datetime.time(9, 0),
                descricao='Reunião Estratégica de Planejamento'
            ),
            Compromisso(
                cidade='Porto União',
                data=hoje,
                hora=datetime.time(14, 0),
                descricao='Auditoria de Processos Operacionais'
            ),
            Compromisso(
                cidade='Porto União',
                data=amanha,
                hora=datetime.time(10, 0),
                descricao='Treinamento de Equipes Setoriais'
            ),
            Compromisso(
                cidade='Florianópolis',
                data=hoje,
                hora=datetime.time(11, 0),
                descricao='Sessão de Alinhamento Executivo'
            ),
            Compromisso(
                cidade='Joinville',
                data=amanha,
                hora=datetime.time(8, 0),
                descricao='Congresso de Inovação Industrial'
            ),
        ]
        db.session.add_all(exemplos_eventos)
        db.session.commit()

# Garante que as tabelas sejam criadas no contexto da aplicação (útil para deploy no Render)
with app.app_context():
    criar_dados_iniciais()

if __name__ == '__main__':
    app.run(debug=True)